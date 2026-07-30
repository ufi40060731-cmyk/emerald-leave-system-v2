from __future__ import annotations

import os
import json
import re
import secrets
from pathlib import Path
import threading
import time
import httpx
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from enum import Enum
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from sqlalchemy import Boolean, Date, DateTime, Integer, String, Text, UniqueConstraint, create_engine, inspect, or_, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from .rag_service import chat_knowledge, search_knowledge, _call_chat_completion
from .schedule_service import (
    CalendarOverrideData,
    RotationSettingsData,
    calculate_leave_days,
    classify_workday,
    upcoming_saturdays,
)

from .holiday_sync import (
    SOURCE_NAME as HOLIDAY_SOURCE_NAME,
    HolidaySourceError,
    fetch_holiday_html,
    parse_holiday_html,
)


def _load_dotenv_file() -> None:
    """Minimal .env loader (no extra dependency) so backend/.env actually takes
    effect. Real OS environment variables always win over the file."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv_file()

DATABASE_URL = (
    os.getenv("DATABASE_URL")
    or os.getenv("MYSQL_URL")
    or "sqlite:///./data/emerald.db"
)

# Railway's MySQL variable commonly uses mysql://. SQLAlchemy needs the
# installed PyMySQL driver to be selected explicitly.
if DATABASE_URL.startswith("mysql://"):
    DATABASE_URL = "mysql+pymysql://" + DATABASE_URL.removeprefix("mysql://")
elif DATABASE_URL.startswith("mysql2://"):
    DATABASE_URL = "mysql+pymysql://" + DATABASE_URL.removeprefix("mysql2://")
SECRET_KEY = os.getenv("EMERALD_SECRET", "change-this-before-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "60"))
THAILAND_TZ = ZoneInfo("Asia/Bangkok")


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


HOLIDAY_AUTO_SYNC_ENABLED = _env_bool("HOLIDAY_AUTO_SYNC_ENABLED", True)
HOLIDAY_AUTO_SYNC_HOUR = int(os.getenv("HOLIDAY_AUTO_SYNC_HOUR", "6"))
HOLIDAY_AUTO_SYNC_MINUTE = int(os.getenv("HOLIDAY_AUTO_SYNC_MINUTE", "30"))
HOLIDAY_AUTO_SYNC_STARTUP_DELAY_SECONDS = float(
    os.getenv("HOLIDAY_AUTO_SYNC_STARTUP_DELAY_SECONDS", "8")
)

if DATABASE_URL.startswith("sqlite:///"):
    sqlite_path = DATABASE_URL.removeprefix("sqlite:///")
    if sqlite_path and sqlite_path != ":memory:":
        Path(sqlite_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine_kwargs = {"connect_args": connect_args, "pool_pre_ping": True}
if DATABASE_URL.startswith("mysql"):
    # MySQL closes idle connections after `wait_timeout` (default 8h, often much
    # lower on managed hosting) - recycle before that so pool_pre_ping never has
    # to silently reconnect mid-request.
    engine_kwargs["pool_recycle"] = 280
engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


class Role(str, Enum):
    employee = "employee"
    manager = "manager"
    hr = "hr"
    admin = "admin"


class LeaveStatus(str, Enum):
    manager_pending = "manager_pending"
    hr_pending = "hr_pending"
    approved = "approved"
    rejected = "rejected"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(20))
    department: Mapped[str] = mapped_column(String(80), default="General")
    rotation_group: Mapped[str] = mapped_column(String(20), default="NONE")
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    photo_data: Mapped[str | None] = mapped_column(Text, nullable=True)


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[str] = mapped_column(String(20), index=True)
    leave_type: Mapped[str] = mapped_column(String(50))
    start_date: Mapped[datetime] = mapped_column(Date)
    end_date: Mapped[datetime] = mapped_column(Date)
    reason: Mapped[str] = mapped_column(String(500), default="")
    workdays: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(30), default=LeaveStatus.manager_pending.value)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )



class RotationSchedule(Base):
    __tablename__ = "rotation_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    name: Mapped[str] = mapped_column(String(100), default="A/B Saturday Rotation")
    anchor_date: Mapped[date] = mapped_column(Date)
    first_working_group: Mapped[str] = mapped_column(String(10), default="A")
    cycle_weeks: Mapped[int] = mapped_column(Integer, default=2)
    saturday_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    sunday_is_day_off: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class CalendarOverride(Base):
    __tablename__ = "calendar_overrides"
    __table_args__ = (
        UniqueConstraint("date", "rotation_group", name="uq_calendar_override_date_group"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    override_type: Mapped[str] = mapped_column(String(20))
    rotation_group: Mapped[str] = mapped_column(String(20), default="ALL")
    note: Mapped[str] = mapped_column(String(300), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class Holiday(Base):
    __tablename__ = "holidays"
    __table_args__ = (
        UniqueConstraint("country", "date", "name", name="uq_holiday_country_date_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    country: Mapped[str] = mapped_column(String(2), default="TH", index=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    date: Mapped[datetime] = mapped_column(Date, index=True)
    name: Mapped[str] = mapped_column(String(160))
    holiday_type: Mapped[str] = mapped_column(String(30), default="official")
    company_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[str] = mapped_column(String(40), default="seed")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class SOPDocument(Base):
    __tablename__ = "sop_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(40), index=True)
    role_scope: Mapped[str] = mapped_column(String(120), default="all")
    title_zh: Mapped[str] = mapped_column(String(180))
    title_en: Mapped[str] = mapped_column(String(180))
    title_th: Mapped[str] = mapped_column(String(180))
    summary_zh: Mapped[str] = mapped_column(String(800), default="")
    summary_en: Mapped[str] = mapped_column(String(800), default="")
    summary_th: Mapped[str] = mapped_column(String(800), default="")
    version: Mapped[str] = mapped_column(String(40), default="1.0")
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    required: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class SOPAcknowledgement(Base):
    __tablename__ = "sop_acknowledgements"
    __table_args__ = (
        UniqueConstraint("user_id", "sop_id", "version", name="uq_sop_ack_user_version"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(20), index=True)
    sop_id: Mapped[int] = mapped_column(Integer, index=True)
    version: Mapped[str] = mapped_column(String(40))
    quiz_score: Mapped[int] = mapped_column(Integer, default=0)
    acknowledged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    __table_args__ = (
        UniqueConstraint("employee_id", "work_date", name="uq_attendance_employee_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[str] = mapped_column(String(20), index=True)
    work_date: Mapped[date] = mapped_column(Date, index=True)
    scheduled_start: Mapped[str] = mapped_column(String(8), default="08:00")
    scheduled_end: Mapped[str] = mapped_column(String(8), default="17:00")
    clock_in: Mapped[str | None] = mapped_column(String(8), nullable=True)
    clock_out: Mapped[str | None] = mapped_column(String(8), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="normal")
    source: Mapped[str] = mapped_column(String(40), default="manual")
    note: Mapped[str] = mapped_column(String(500), default="")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class AttendanceCorrection(Base):
    __tablename__ = "attendance_corrections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    attendance_id: Mapped[int] = mapped_column(Integer, index=True)
    employee_id: Mapped[str] = mapped_column(String(20), index=True)
    requested_clock_in: Mapped[str | None] = mapped_column(String(8), nullable=True)
    requested_clock_out: Mapped[str | None] = mapped_column(String(8), nullable=True)
    reason: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    reviewed_by: Mapped[str | None] = mapped_column(String(20), nullable=True)
    review_note: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class EnterpriseAuditEvent(Base):
    __tablename__ = "enterprise_audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor_id: Mapped[str] = mapped_column(String(20), index=True)
    action: Mapped[str] = mapped_column(String(80), index=True)
    resource: Mapped[str] = mapped_column(String(80), default="")
    resource_id: Mapped[str] = mapped_column(String(80), default="")
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class WorkRule(Base):
    __tablename__ = "work_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(40), index=True)
    content_zh: Mapped[str] = mapped_column(Text)
    source_document: Mapped[str] = mapped_column(
        String(200), default="Emerald_工作規章_繁體中文譯本.pdf"
    )
    source_page: Mapped[int] = mapped_column(Integer, default=1)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class OnboardingItem(Base):
    __tablename__ = "onboarding_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    title_zh: Mapped[str] = mapped_column(String(300))
    title_en: Mapped[str] = mapped_column(String(300), default="")
    title_th: Mapped[str] = mapped_column(String(300), default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class OnboardingProgress(Base):
    __tablename__ = "onboarding_progress"
    __table_args__ = (UniqueConstraint("user_id", "item_id", name="uq_onboarding_progress_user_item"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(20), index=True)
    item_id: Mapped[int] = mapped_column(Integer, index=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


class LoginRequest(BaseModel):
    account: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserCreate(BaseModel):
    id: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=100)
    role: Role = Role.employee
    department: str = Field(
        default="General",
        min_length=1,
        max_length=80,
    )
    rotation_group: str = Field(
        default="NONE",
        pattern="^(A|B|NONE)$",
    )
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    id: str
    name: str
    role: str
    department: str
    rotation_group: str
    is_active: bool
    photo_data: str | None = None

    model_config = {"from_attributes": True}

class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class AdminPasswordResetRequest(BaseModel):
    new_password: str = Field(min_length=8, max_length=128)


class WorkRuleOut(BaseModel):
    id: int
    code: str
    title: str
    category: str
    content_zh: str
    source_document: str
    source_page: int
    sort_order: int
    active: bool
    updated_at: datetime

    model_config = {"from_attributes": True}


class WorkRuleCreate(BaseModel):
    code: str = Field(min_length=1, max_length=30)
    title: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=40)
    content_zh: str = Field(min_length=1)
    sort_order: int = 0


class WorkRuleUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    category: str | None = Field(default=None, min_length=1, max_length=40)
    content_zh: str | None = Field(default=None, min_length=1)
    sort_order: int | None = None
    active: bool | None = None


class OnboardingItemOut(BaseModel):
    id: int
    code: str
    title_zh: str
    title_en: str
    title_th: str
    sort_order: int
    active: bool
    updated_at: datetime

    model_config = {"from_attributes": True}


class OnboardingItemCreate(BaseModel):
    code: str = Field(min_length=1, max_length=40)
    title_zh: str = Field(min_length=1, max_length=300)
    title_en: str = Field(default="", max_length=300)
    title_th: str = Field(default="", max_length=300)
    sort_order: int = 0


class OnboardingItemUpdate(BaseModel):
    title_zh: str | None = Field(default=None, min_length=1, max_length=300)
    title_en: str | None = Field(default=None, max_length=300)
    title_th: str | None = Field(default=None, max_length=300)
    sort_order: int | None = None
    active: bool | None = None


class OnboardingProgressUpdate(BaseModel):
    completed: bool


class LeaveCreate(BaseModel):
    leave_type: str = Field(min_length=1, max_length=50)
    start_date: date
    end_date: date
    reason: str = Field(default="", max_length=500)


class LeaveOut(BaseModel):
    id: int
    employee_id: str
    leave_type: str
    start_date: date
    end_date: date
    reason: str
    workdays: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}



class RotationSettingsOut(BaseModel):
    name: str
    anchor_date: date
    first_working_group: str
    cycle_weeks: int
    saturday_enabled: bool
    sunday_is_day_off: bool

    model_config = {"from_attributes": True}


class RotationSettingsUpdate(BaseModel):
    name: str = Field(default="A/B Saturday Rotation", min_length=1, max_length=100)
    anchor_date: date
    first_working_group: str = Field(default="A", pattern="^(A|B)$")
    cycle_weeks: int = Field(default=2, ge=2, le=12)
    saturday_enabled: bool = True
    sunday_is_day_off: bool = True


class LeaveCalculateRequest(BaseModel):
    start_date: date
    end_date: date


class RotationGroupUpdate(BaseModel):
    rotation_group: str = Field(pattern="^(A|B|NONE)$")


class CalendarOverrideCreate(BaseModel):
    date: date
    override_type: str = Field(pattern="^(WORKDAY|DAY_OFF)$")
    rotation_group: str = Field(default="ALL", pattern="^(ALL|A|B|NONE)$")
    note: str = Field(default="", max_length=300)


class CalendarOverrideOut(BaseModel):
    id: int
    date: date
    override_type: str
    rotation_group: str
    note: str

    model_config = {"from_attributes": True}


class HolidayOut(BaseModel):
    id: int
    country: str
    year: int
    date: datetime
    name: str
    holiday_type: str
    company_confirmed: bool
    source: str

    model_config = {"from_attributes": True}


class HolidayConfirmRequest(BaseModel):
    company_confirmed: bool


class HolidayCreate(BaseModel):
    country: str = Field(default="TH", min_length=2, max_length=2)
    date: datetime
    name: str = Field(min_length=1, max_length=160)
    holiday_type: str = Field(default="company", max_length=30)
    company_confirmed: bool = True


class RagSearchRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1000)
    top_k: int = Field(default=3, ge=1, le=5)


class RagChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=2000)


class RagChatRequest(BaseModel):
    message: str = Field(min_length=2, max_length=2000)
    history: list[RagChatMessage] = Field(default_factory=list, max_length=12)
    top_k: int = Field(default=3, ge=1, le=5)
    language: str = Field(default="zh-TW", pattern="^(zh-TW|en|th)$")


class SOPOut(BaseModel):
    id: int
    code: str
    category: str
    role_scope: str
    title_zh: str
    title_en: str
    title_th: str
    summary_zh: str
    summary_en: str
    summary_th: str
    version: str
    effective_date: date | None
    status: str
    required: bool
    sort_order: int

    model_config = {"from_attributes": True}


class SOPCreate(BaseModel):
    code: str = Field(min_length=1, max_length=30)
    category: str = Field(min_length=1, max_length=40)
    role_scope: str = Field(default="all", max_length=120)
    title_zh: str = Field(min_length=1, max_length=180)
    title_en: str = Field(default="", max_length=180)
    title_th: str = Field(default="", max_length=180)
    summary_zh: str = Field(default="", max_length=800)
    summary_en: str = Field(default="", max_length=800)
    summary_th: str = Field(default="", max_length=800)
    version: str = Field(default="1.0", max_length=40)
    status: str = Field(default="draft", pattern="^(draft|published)$")
    required: bool = True
    sort_order: int = 0


class SOPUpdate(BaseModel):
    category: str | None = Field(default=None, max_length=40)
    role_scope: str | None = Field(default=None, max_length=120)
    title_zh: str | None = Field(default=None, max_length=180)
    title_en: str | None = Field(default=None, max_length=180)
    title_th: str | None = Field(default=None, max_length=180)
    summary_zh: str | None = Field(default=None, max_length=800)
    summary_en: str | None = Field(default=None, max_length=800)
    summary_th: str | None = Field(default=None, max_length=800)
    version: str | None = Field(default=None, max_length=40)
    status: str | None = Field(default=None, pattern="^(draft|published)$")
    required: bool | None = None
    sort_order: int | None = None


class SOPAcknowledgementCreate(BaseModel):
    quiz_score: int = Field(ge=0, le=100)
    passing_score: int = Field(default=80, ge=60, le=100)


class AttendanceRecordInput(BaseModel):
    employee_id: str = Field(min_length=1, max_length=20)
    work_date: date
    scheduled_start: str = Field(default="08:00", max_length=8)
    scheduled_end: str = Field(default="17:00", max_length=8)
    clock_in: str | None = Field(default=None, max_length=8)
    clock_out: str | None = Field(default=None, max_length=8)
    status: str = Field(default="normal", pattern="^(normal|late|early_leave|missing_punch|absent|day_off)$")
    source: str = Field(default="import", max_length=40)
    note: str = Field(default="", max_length=500)


class AttendanceImportRequest(BaseModel):
    records: list[AttendanceRecordInput] = Field(min_length=1, max_length=5000)


class AttendanceOut(BaseModel):
    id: int
    employee_id: str
    work_date: date
    scheduled_start: str
    scheduled_end: str
    clock_in: str | None
    clock_out: str | None
    status: str
    source: str
    note: str

    model_config = {"from_attributes": True}


class AttendanceCorrectionCreate(BaseModel):
    requested_clock_in: str | None = Field(default=None, max_length=8)
    requested_clock_out: str | None = Field(default=None, max_length=8)
    reason: str = Field(min_length=3, max_length=500)


class AttendanceCorrectionReview(BaseModel):
    status: str = Field(pattern="^(approved|rejected)$")
    review_note: str = Field(default="", max_length=500)


class AttendanceCorrectionOut(BaseModel):
    id: int
    attendance_id: int
    employee_id: str
    requested_clock_in: str | None
    requested_clock_out: str | None
    reason: str
    status: str
    reviewed_by: str | None
    review_note: str
    created_at: datetime
    reviewed_at: datetime | None

    model_config = {"from_attributes": True}


def _rotation_settings_data(item: RotationSchedule) -> RotationSettingsData:
    return RotationSettingsData(
        anchor_date=item.anchor_date,
        first_working_group=item.first_working_group,
        cycle_weeks=item.cycle_weeks,
        saturday_enabled=item.saturday_enabled,
        sunday_is_day_off=item.sunday_is_day_off,
    )


def _override_data(items: list[CalendarOverride]) -> list[CalendarOverrideData]:
    return [
        CalendarOverrideData(
            target_date=item.date,
            override_type=item.override_type,
            rotation_group=item.rotation_group,
            note=item.note,
        )
        for item in items
    ]


def get_rotation_schedule(db: Session) -> RotationSchedule:
    item = db.get(RotationSchedule, 1)
    if item is None:
        item = RotationSchedule(
            id=1,
            name="A/B Saturday Rotation",
            anchor_date=date(2026, 1, 3),
            first_working_group="A",
            cycle_weeks=2,
            saturday_enabled=True,
            sunday_is_day_off=True,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
    return item


def get_calendar_overrides(
    db: Session, start_date: date | None = None, end_date: date | None = None
) -> list[CalendarOverride]:
    stmt = select(CalendarOverride).order_by(CalendarOverride.date, CalendarOverride.rotation_group)
    if start_date is not None:
        stmt = stmt.where(CalendarOverride.date >= start_date)
    if end_date is not None:
        stmt = stmt.where(CalendarOverride.date <= end_date)
    return list(db.scalars(stmt))


def holiday_dates_between(db: Session, start_date: date, end_date: date) -> set[date]:
    stmt = select(Holiday.date).where(
        Holiday.country == "TH", Holiday.date >= start_date, Holiday.date <= end_date
    )
    return set(db.scalars(stmt))


def calculate_user_leave(
    db: Session, user: User, start_date: date, end_date: date
) -> dict:
    schedule = get_rotation_schedule(db)
    overrides = get_calendar_overrides(db, start_date, end_date)
    holidays = holiday_dates_between(db, start_date, end_date)
    return calculate_leave_days(
        start_date=start_date,
        end_date=end_date,
        rotation_group=user.rotation_group,
        settings=_rotation_settings_data(schedule),
        holidays=holidays,
        overrides=_override_data(overrides),
    )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_access_token(subject: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        account = payload.get("sub")
        if not account:
            raise ValueError("missing subject")
    except (JWTError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc

    user = db.get(User, account)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="This account has been deactivated")
    return user


def require_roles(*roles: Role):
    def checker(user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role not in {role.value for role in roles}:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return checker



THAI_HOLIDAY_SEED = {
    # Offline fallback set. Automatic synchronization replaces/updates these rows.
    # HR should still review and confirm the dates used by the company.
    2026: [
        ("2026-01-01", "公曆新年"),
        ("2026-01-02", "特別假期"),
        ("2026-03-03", "萬佛節"),
        ("2026-04-06", "恰克里王朝開國紀念日"),
        ("2026-04-13", "宋干節（潑水節）"),
        ("2026-04-14", "宋干節（潑水節）"),
        ("2026-04-15", "宋干節（潑水節）"),
        ("2026-05-01", "勞動節"),
        ("2026-05-04", "泰王登基紀念日"),
        ("2026-05-13", "春耕節"),
        ("2026-05-31", "佛誕節"),
        ("2026-06-01", "佛誕節（補假）"),
        ("2026-06-03", "蘇提達王后誕辰日"),
        ("2026-07-28", "國王瓦吉拉隆功誕辰日"),
        ("2026-07-29", "三寶佛節"),
        ("2026-07-30", "守夏節"),
        ("2026-08-12", "詩麗吉王太后誕辰日（母親節）"),
        ("2026-10-13", "拉瑪九世國王逝世紀念日"),
        ("2026-10-16", "特別假期（僅曼谷）"),
        ("2026-10-23", "朱拉隆功大帝紀念日"),
        ("2026-12-05", "拉瑪九世國王普密蓬·阿杜德誕辰紀念日（父親節）"),
        ("2026-12-07", "拉瑪九世國王普密蓬·阿杜德誕辰紀念日（父親節）（補假）"),
        ("2026-12-10", "泰國憲法紀念日"),
        ("2026-12-31", "元旦前夕"),
    ]
}


def ensure_year_exists(db: Session, year: int, country: str = "TH") -> int:
    existing = db.scalar(
        select(Holiday.id).where(Holiday.country == country, Holiday.year == year).limit(1)
    )
    if existing:
        return 0

    rows = THAI_HOLIDAY_SEED.get(year, [])
    for date_text, name in rows:
        db.add(
            Holiday(
                country=country,
                year=year,
                date=datetime.fromisoformat(date_text).date(),
                name=name,
                holiday_type="official",
                company_confirmed=False,
                source="seed",
            )
        )
    db.commit()
    return len(rows)


HOLIDAY_SYNC_MANAGED_SOURCES = {
    "seed",
    HOLIDAY_SOURCE_NAME,
    f"{HOLIDAY_SOURCE_NAME}:removed",
}


def sync_holiday_year(db: Session, year: int, country: str = "TH") -> dict:
    html, source_url = fetch_holiday_html(year)
    candidates = parse_holiday_html(html, year)
    normalized_country = country.upper()

    existing = list(
        db.scalars(
            select(Holiday).where(
                Holiday.country == normalized_country,
                Holiday.year == year,
            )
        )
    )
    managed = [item for item in existing if item.source in HOLIDAY_SYNC_MANAGED_SOURCES]
    unmatched_managed = {item.id: item for item in managed}

    added = 0
    updated = 0
    unchanged = 0
    deleted = 0
    retained_confirmed = 0

    for candidate in candidates:
        exact = next(
            (
                item
                for item in existing
                if item.date == candidate.date and item.name == candidate.name
            ),
            None,
        )
        item = exact
        if item is None:
            item = next(
                (
                    row
                    for row in unmatched_managed.values()
                    if row.date == candidate.date
                ),
                None,
            )

        if item is None:
            item = Holiday(
                country=normalized_country,
                year=year,
                date=candidate.date,
                name=candidate.name,
                holiday_type="official",
                company_confirmed=False,
                source=HOLIDAY_SOURCE_NAME,
            )
            db.add(item)
            existing.append(item)
            added += 1
            continue

        if item.id in unmatched_managed:
            unmatched_managed.pop(item.id, None)

        if item.source not in HOLIDAY_SYNC_MANAGED_SOURCES:
            # An identical company/manual holiday already exists. Do not create a duplicate.
            unchanged += 1
            continue

        changed = False
        if item.name != candidate.name:
            item.name = candidate.name
            changed = True
        if item.holiday_type != "official":
            item.holiday_type = "official"
            changed = True
        if item.source != HOLIDAY_SOURCE_NAME:
            item.source = HOLIDAY_SOURCE_NAME
            changed = True
        if changed:
            updated += 1
        else:
            unchanged += 1

    for item in unmatched_managed.values():
        if item.company_confirmed:
            # Never silently remove a date HR has already approved for the company.
            item.source = f"{HOLIDAY_SOURCE_NAME}:removed"
            retained_confirmed += 1
        else:
            db.delete(item)
            deleted += 1

    db.commit()
    return {
        "year": year,
        "country": normalized_country,
        "source": HOLIDAY_SOURCE_NAME,
        "source_url": source_url,
        "fetched": len(candidates),
        "added": added,
        "updated": updated,
        "unchanged": unchanged,
        "deleted": deleted,
        "retained_confirmed": retained_confirmed,
    }


def sync_current_and_next_years(db: Session) -> dict:
    current_year = datetime.now(THAILAND_TZ).year
    results: list[dict] = []
    errors: list[dict] = []
    for year in (current_year, current_year + 1):
        try:
            results.append(sync_holiday_year(db, year))
        except HolidaySourceError as exc:
            # Keep the existing fallback data if the publisher has not released
            # the next year yet or the source is temporarily unavailable.
            ensure_year_exists(db, year)
            errors.append({"year": year, "error": str(exc)})
    return {"results": results, "errors": errors}


_holiday_scheduler_stop = threading.Event()
_holiday_scheduler_thread: threading.Thread | None = None
_holiday_scheduler_guard = threading.Lock()
_holiday_sync_run_guard = threading.Lock()
_holiday_sync_state_guard = threading.Lock()
_holiday_sync_state: dict = {
    "running": False,
    "last_trigger": None,
    "last_started_at": None,
    "last_finished_at": None,
    "last_status": "not_run",
    "last_result": None,
    "last_error": None,
}


def _iso_bangkok(value: datetime | None = None) -> str:
    current = value or datetime.now(THAILAND_TZ)
    return current.astimezone(THAILAND_TZ).isoformat(timespec="seconds")


def _next_holiday_sync_at(now: datetime | None = None) -> datetime:
    current = (now or datetime.now(THAILAND_TZ)).astimezone(THAILAND_TZ)
    target = current.replace(
        hour=HOLIDAY_AUTO_SYNC_HOUR,
        minute=HOLIDAY_AUTO_SYNC_MINUTE,
        second=0,
        microsecond=0,
    )
    if target <= current:
        target += timedelta(days=1)
    return target


def _set_holiday_sync_state(**changes) -> None:  # type: ignore[no-untyped-def]
    with _holiday_sync_state_guard:
        _holiday_sync_state.update(changes)


def execute_holiday_auto_sync(trigger: str, db: Session | None = None) -> dict:
    """Run current/next-year synchronization and record a status snapshot."""

    with _holiday_sync_run_guard:
        started_at = datetime.now(THAILAND_TZ)
        _set_holiday_sync_state(
            running=True,
            last_trigger=trigger,
            last_started_at=_iso_bangkok(started_at),
            last_finished_at=None,
            last_status="running",
            last_error=None,
        )
        owns_session = db is None
        session = db or SessionLocal()
        try:
            result = sync_current_and_next_years(session)
            status_text = "completed_with_warnings" if result.get("errors") else "completed"
            _set_holiday_sync_state(
                running=False,
                last_finished_at=_iso_bangkok(),
                last_status=status_text,
                last_result=result,
                last_error=None,
            )
            return result
        except Exception as exc:
            _set_holiday_sync_state(
                running=False,
                last_finished_at=_iso_bangkok(),
                last_status="failed",
                last_error=str(exc),
            )
            raise
        finally:
            if owns_session:
                session.close()


def _holiday_scheduler_loop() -> None:
    if HOLIDAY_AUTO_SYNC_STARTUP_DELAY_SECONDS > 0:
        if _holiday_scheduler_stop.wait(HOLIDAY_AUTO_SYNC_STARTUP_DELAY_SECONDS):
            return

    try:
        execute_holiday_auto_sync("startup")
    except Exception:
        # The service remains available and retries at the next scheduled time.
        pass

    while not _holiday_scheduler_stop.is_set():
        now = datetime.now(THAILAND_TZ)
        target = _next_holiday_sync_at(now)
        wait_seconds = max((target - now).total_seconds(), 1.0)
        if _holiday_scheduler_stop.wait(wait_seconds):
            return
        try:
            execute_holiday_auto_sync("daily_schedule")
        except Exception:
            # Keep the scheduler alive after a temporary network/database failure.
            time.sleep(1)


def start_holiday_scheduler() -> None:
    global _holiday_scheduler_thread
    if not HOLIDAY_AUTO_SYNC_ENABLED:
        return
    if not 0 <= HOLIDAY_AUTO_SYNC_HOUR <= 23:
        raise RuntimeError("HOLIDAY_AUTO_SYNC_HOUR must be between 0 and 23")
    if not 0 <= HOLIDAY_AUTO_SYNC_MINUTE <= 59:
        raise RuntimeError("HOLIDAY_AUTO_SYNC_MINUTE must be between 0 and 59")

    with _holiday_scheduler_guard:
        if _holiday_scheduler_thread and _holiday_scheduler_thread.is_alive():
            return
        _holiday_scheduler_stop.clear()
        _holiday_scheduler_thread = threading.Thread(
            target=_holiday_scheduler_loop,
            name="emerald-thailand-holiday-sync",
            daemon=True,
        )
        _holiday_scheduler_thread.start()


def stop_holiday_scheduler() -> None:
    global _holiday_scheduler_thread
    _holiday_scheduler_stop.set()
    with _holiday_scheduler_guard:
        thread = _holiday_scheduler_thread
        _holiday_scheduler_thread = None
    if thread and thread.is_alive():
        thread.join(timeout=2)


def require_holiday_sync_key(
    x_holiday_sync_key: Annotated[
        str | None, Header(alias="X-Holiday-Sync-Key")
    ] = None,
) -> None:
    expected = os.getenv("HOLIDAY_SYNC_KEY", "").strip()
    if not expected:
        raise HTTPException(status_code=503, detail="HOLIDAY_SYNC_KEY is not configured")
    if not x_holiday_sync_key or not secrets.compare_digest(x_holiday_sync_key, expected):
        raise HTTPException(status_code=401, detail="Invalid holiday sync key")


def bootstrap_calendar_years() -> None:
    current_year = datetime.now(THAILAND_TZ).year
    with SessionLocal() as db:
        # Always ensure the current and next year have fallback containers.
        ensure_year_exists(db, current_year)
        ensure_year_exists(db, current_year + 1)


def ensure_schema_compatibility() -> None:
    """Add v15.2 columns for databases created by earlier demo versions.

    This small compatibility layer is intentionally conservative. Production users
    should replace it with Alembic migrations before a real rollout.
    """

    inspector = inspect(engine)
    migrations = {
        "users": {
            "department": "VARCHAR(80) DEFAULT 'General'",
            "rotation_group": "VARCHAR(20) DEFAULT 'NONE'",
            "is_active": "BOOLEAN DEFAULT 1",
            "photo_data": "TEXT",
        },
        "leave_requests": {
            "workdays": "INTEGER DEFAULT 0",
        },
    }
    with engine.begin() as connection:
        for table_name, columns in migrations.items():
            if table_name not in inspector.get_table_names():
                continue
            existing = {column["name"] for column in inspector.get_columns(table_name)}
            for column_name, definition in columns.items():
                if column_name not in existing:
                    connection.execute(
                        text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")
                    )


ONBOARDING_ITEM_SEED = [
    {"code": "COMPANY", "title_zh": "了解公司、廠區與主要產品", "title_en": "Learn the company, site, and main products", "title_th": "ทำความรู้จักบริษัท สถานที่ และผลิตภัณฑ์หลัก", "sort_order": 1},
    {"code": "ATTENDANCE", "title_zh": "確認上下班、打卡、遲到與早退規定", "title_en": "Confirm work hours, clock-in, lateness, and early-leave rules", "title_th": "ยืนยันเวลางาน การลงเวลา การมาสาย และการกลับก่อนเวลา", "sort_order": 2},
    {"code": "ROTATION", "title_zh": "確認自己的 A／B 組星期六輪班", "title_en": "Confirm your A/B Saturday rotation group", "title_th": "ยืนยันกลุ่มเวรวันเสาร์ A/B ของคุณ", "sort_order": 3},
    {"code": "LEAVE", "title_zh": "閱讀請假種類、證明與審核流程", "title_en": "Read leave types, evidence, and approval workflow", "title_th": "อ่านประเภทการลา หลักฐาน และขั้นตอนอนุมัติ", "sort_order": 4},
    {"code": "SAFETY", "title_zh": "完成工廠安全、PPE 與緊急通報說明", "title_en": "Complete factory safety, PPE, and emergency reporting guidance", "title_th": "เรียนรู้ความปลอดภัย PPE และการรายงานเหตุฉุกเฉิน", "sort_order": 5},
    {"code": "QUALITY", "title_zh": "了解衛生、品質與生產區進出要求", "title_en": "Understand hygiene, quality, and production-area entry requirements", "title_th": "เข้าใจสุขอนามัย คุณภาพ และข้อกำหนดการเข้าพื้นที่ผลิต", "sort_order": 6},
    {"code": "CONFIDENTIALITY", "title_zh": "了解保密、拍照、手機與公司資料規定", "title_en": "Understand confidentiality, photography, phones, and company-data rules", "title_th": "เข้าใจกฎความลับ การถ่ายภาพ โทรศัพท์ และข้อมูลบริษัท", "sort_order": 7},
    {"code": "CONTACTS", "title_zh": "記下直屬主管、HR 與緊急聯絡方式", "title_en": "Record your manager, HR, and emergency contacts", "title_th": "บันทึกผู้บังคับบัญชา HR และผู้ติดต่อฉุกเฉิน", "sort_order": 8},
]


def seed_onboarding_items(db: Session) -> dict:
    created = 0
    for row in ONBOARDING_ITEM_SEED:
        if db.scalar(select(OnboardingItem).where(OnboardingItem.code == row["code"])) is None:
            db.add(OnboardingItem(**row))
            created += 1
    db.commit()
    return {"created": created, "total": len(ONBOARDING_ITEM_SEED)}


WORK_RULE_SEED = [
    {
        "code": "PURPOSE",
        "title": "目的",
        "category": "general",
        "content_zh": "本工作規章旨在制定一套標準作業手冊，供公司全體員工正確遵循，並要求所有員工嚴格遵守。",
        "source_page": 1,
        "sort_order": 1
    },
    {
        "code": "SCOPE",
        "title": "適用範圍",
        "category": "general",
        "content_zh": "本工作規章適用於公司全體員工，內容包括公司所訂定的懲處規定與提供的福利。",
        "source_page": 1,
        "sort_order": 2
    },
    {
        "code": "DEFINITIONS",
        "title": "名詞定義",
        "category": "general",
        "content_zh": "- **生產線員工**：指從事生產、裁切、縫製、封合、包裝、無塵室、品質管制（QC）、倉庫（Store）、清潔及技術維修等工作的員工。\n- **辦公室員工**：指固定在辦公室（Office）工作，且不直接參與生產作業的員工。",
        "source_page": 1,
        "sort_order": 3
    },
    {
        "code": "1",
        "title": "第 1 條：求職文件真實性",
        "category": "employment",
        "content_zh": "求職申請所附文件必須真實。如查明有虛假情形，公司將依情節予以適當處分。",
        "source_page": 1,
        "sort_order": 4
    },
    {
        "code": "2",
        "title": "第 2 條：職務調整",
        "category": "employment",
        "content_zh": "員工原則上應執行其固定職務；如公司評估員工具備執行其他職務的能力，公司得視情況適當調整其職位或工作內容。",
        "source_page": 1,
        "sort_order": 5
    },
    {
        "code": "3",
        "title": "第 3 條：上班、午休、下班與加班時間",
        "category": "attendance",
        "content_zh": "上班時間為 08:00；午休時間為 12:00 至 13:00；下班時間為 17:00。加班前休息時間為 17:00 至 17:30，加班自 17:31 起，至雙方約定時間為止，但不得超過法律規定的上限。",
        "source_page": 1,
        "sort_order": 6
    },
    {
        "code": "4",
        "title": "第 4 條：制服、識別證與飾品",
        "category": "workplace",
        "content_zh": "員工進入公司時，必須穿著公司提供的制服，並於每次上班前佩戴員工識別證。進入生產部門時，禁止佩戴戒指、耳環、手環等飾品。",
        "source_page": 1,
        "sort_order": 7
    },
    {
        "code": "5",
        "title": "第 5 條：尚未領取制服者的服裝規定",
        "category": "workplace",
        "content_zh": "尚未領取制服的員工，服裝應端莊整潔並便於工作。生產部門男女員工均須穿白色上衣，不得穿細肩帶、無袖或過度透薄的上衣；下身須穿長褲，不得穿短褲、五分褲、七分褲、緊身褲或色彩過於鮮豔的褲子進入公司。辦公室女性員工可穿裙子上班，但不得過短，款式與顏色應端莊得體。",
        "source_page": 2,
        "sort_order": 8
    },
    {
        "code": "6",
        "title": "第 6 條：生產線制服、帽子、指甲與鞋子",
        "category": "workplace",
        "content_zh": "生產線員工上班時，必須依公司規定穿著制服及帽子；指甲須經常修剪並保持短而清潔；並須穿著公司提供的鞋子，且隨時保持工作服與鞋子的清潔。",
        "source_page": 2,
        "sort_order": 9
    },
    {
        "code": "7",
        "title": "第 7 條：生產部門禁止攜入物品",
        "category": "workplace",
        "content_zh": "生產線員工嚴禁將食物、水、零食、飯食或個人物品帶入生產部門，例如粉餅、口紅、口服藥、外用藥及行動電話等。",
        "source_page": 2,
        "sort_order": 10
    },
    {
        "code": "8",
        "title": "第 8 條：吸菸",
        "category": "discipline",
        "content_zh": "公司僅允許在指定地點吸菸；未依規定辦理者，視為嚴重違反紀律。",
        "source_page": 2,
        "sort_order": 11
    },
    {
        "code": "9",
        "title": "第 9 條：酒類、致醉飲品、毒品與賭博",
        "category": "discipline",
        "content_zh": "嚴禁在工廠內飲酒、飲用其他致醉飲品、施用毒品或賭博；亦禁止攜帶、買賣酒類或毒品。如經查獲，將立即終止員工身分，並由公司報警依法處理。處於醉酒狀態或身體狀況不適合工作的員工，當日不得進入公司上班。",
        "source_page": 2,
        "sort_order": 12
    },
    {
        "code": "10",
        "title": "第 10 條：危險武器",
        "category": "discipline",
        "content_zh": "嚴禁攜帶危險武器進入公司或生產部門。如經查獲，將終止員工身分，並由公司報警依法處理。",
        "source_page": 2,
        "sort_order": 13
    },
    {
        "code": "11",
        "title": "第 11 條：鬥毆與衝突",
        "category": "discipline",
        "content_zh": "嚴禁在公司內鬥毆或引發衝突；如經查獲，視為違規並終止員工身分。",
        "source_page": 2,
        "sort_order": 14
    },
    {
        "code": "12",
        "title": "第 12 條：兵役文件",
        "category": "employment",
        "content_zh": "已完成兵役義務的男性員工，應配合提交相關文件供公司留存。尚未到服役期限或依法緩徵者，亦須提出證明文件或事先通知公司。如公司查明未依規定辦理，將視為違規並終止員工身分。",
        "source_page": 2,
        "sort_order": 15
    },
    {
        "code": "13",
        "title": "第 13 條：公司名譽、財產、舞弊、資料與工作損失",
        "category": "discipline",
        "content_zh": "如員工造成公司名譽或財產受損、涉及舞弊，或洩漏公司資料，以及因故意或疏忽造成工作錯誤或公司損失，均視為違規；公司將依實際損害的嚴重程度，酌情決定處分。",
        "source_page": 2,
        "sort_order": 16
    },
    {
        "code": "14",
        "title": "第 14 條：公司文件與公告",
        "category": "employment",
        "content_zh": "公司文件、公告板及公告均屬公司財產；員工如有毀損或違反相關規定，視為違規。",
        "source_page": 2,
        "sort_order": 17
    },
    {
        "code": "15",
        "title": "第 15 條：試用期",
        "category": "employment",
        "content_zh": "試用期為 119 天，且員工必須通過公司的工作評估。未達評估標準者，視為未通過試用期，後續處理由公司決定。",
        "source_page": 2,
        "sort_order": 18
    },
    {
        "code": "16.1.1",
        "title": "16.1.1 病假 1 天",
        "category": "sick_leave",
        "content_zh": "請病假 1 天時，員工須於當日上午 09:00 前先通知公司。請假方式及應附文件如下：\n\n1. 員工本人須於 09:00 前致電通知直屬主管及人力資源部門，以避免影響連續性工作。\n2. 應提供由具合法資格之現代醫學醫師開立的醫療證明（如有，應提交正本）。\n3. 返回工作崗位後，員工須於 24 小時內完成請假單。",
        "source_page": 3,
        "sort_order": 19
    },
    {
        "code": "16.1.2",
        "title": "16.1.2 病假 2 天以上",
        "category": "sick_leave",
        "content_zh": "病假達 2 天以上者，僅接受醫院內具合法資格之現代醫學醫師開立的醫療證明；員工並須每天於 09:00 前致電通知直屬主管及人力資源部門，直到能恢復正常上班為止。",
        "source_page": 3,
        "sort_order": 20
    },
    {
        "code": "16.2.1",
        "title": "16.2.1 事假 1 天",
        "category": "personal_leave",
        "content_zh": "請事假 1 天，須至少提前 2 天提出申請。若屬緊急事件，須於 09:00 前致電通知直屬主管及人力資源部門，以避免影響連續性工作；返回上班當日並須於 24 小時內完成請假單。",
        "source_page": 3,
        "sort_order": 21
    },
    {
        "code": "16.2.2",
        "title": "16.2.2 事假 2 天以上",
        "category": "personal_leave",
        "content_zh": "請事假 2 天以上，須至少提前 7 天提出申請。\n\n**事假備註**：每年事假不得超過 6 天；事假當日不支薪。每次請事假均須附具相關證明，供公司重新審酌是否適當。",
        "source_page": 3,
        "sort_order": 22
    },
    {
        "code": "16.3.1",
        "title": "16.3.1 年假申請與額度",
        "category": "annual_leave",
        "content_zh": "員工自到職日起，依比例取得年假權利，每年最多 6 天。每次可申請 1 天，須提前 7 天通知；每月最多可請 2 天。年假須於當年度使用，不得累積至次年度。公司保留核准或不核准之權利。\n\n**病假、事假與年假共同備註**：\n\n- 第 16.1、16.2 及 16.3 項所列假別，均須經公司核准後方可休假。\n- 不得於國定假日前後連續請假，例如在假日前後的星期六或星期一請假。\n- 每次請假均會影響全勤獎金及特別獎金。\n- 病假或緊急事假須於 09:00 前通知人力資源部門，並在返回上班當日的 24 小時內完成請假單。\n- 未獲公司核准而當日未到班者，公司將視為曠職。",
        "source_page": 3,
        "sort_order": 23
    },
    {
        "code": "16.4.1",
        "title": "16.4.1 生產部門員工",
        "category": "resignation",
        "content_zh": "適用於生產部門員工，主管級除外；主管級依第 16.4.2 項辦理。\n\n- 任職未滿 90 天：須提前 3 天提出離職通知。\n- 任職滿 90 天以上：須提前 15 天提出離職通知。\n- QC、CN、M&E、ST 等按日計薪人員，或在辦公室工作者：須提前 30 天提出離職通知。",
        "source_page": 3,
        "sort_order": 24
    },
    {
        "code": "16.4.2",
        "title": "16.4.2 非生產部門、財產／財務責任及按月計薪員工",
        "category": "resignation",
        "content_zh": "- 任職未滿 90 天：須提前 15 天提出離職通知。\n- 任職超過 90 天：須提前 30 天提出離職通知。\n- 任職滿 1 至 2 年：須提前 45 天提出離職通知。\n- 任職滿 2 至 4 年：須提前 60 天提出離職通知。\n- 任職滿 4 年以上：須提前 90 天提出離職通知。\n\n**離職備註**：公司保留依個別情況判斷是否適當之權利。",
        "source_page": 4,
        "sort_order": 25
    },
    {
        "code": "17",
        "title": "第 17 條：警告處分",
        "category": "discipline",
        "content_zh": "員工未遵守公司規章時，公司得依情況記錄違規並發出警告，處理方式如下：\n\n1. 第 1 次警告：口頭警告（另作書面紀錄）。\n2. 第 2 次警告：視為第二級違規警告。\n3. 第 3 次警告：停職 3 天，或由公司視情況決定更長的停職期間。\n4. 第 4 次警告：終止員工身分。\n\n**備註**：如員工收到警告單但拒絕簽名承認，公司將在公告板張貼至少 1 天，以通知員工該行為違反公司規章，防止再犯，並避免其他員工仿效。",
        "source_page": 4,
        "sort_order": 26
    },
    {
        "code": "18",
        "title": "第 18 條：連續假期後到班與國定假日前後請假",
        "category": "discipline",
        "content_zh": "公司連續放假多日時，員工必須於公司指定恢復上班之日到班；不得在國定假日前後請假。",
        "source_page": 4,
        "sort_order": 27
    },
    {
        "code": "19",
        "title": "第 19 條：已同意加班後未到班、取消與代簽",
        "category": "attendance",
        "content_zh": "如公司已事先通知加班，且員工已簽名同意並申請加班，但之後未到班加班，將視為違規。員工如需取消或請假不加班，須於 15:00 前通知人力資源部門，由其轉知公司。加班同意僅能由本人簽名，嚴禁代他人簽名；代簽行為屬違反紀律，將依違規情節處分。",
        "source_page": 4,
        "sort_order": 28
    },
    {
        "code": "20",
        "title": "第 20 條：刷卡與代刷卡",
        "category": "attendance",
        "content_zh": "所有員工均須依公司規定刷卡，以記錄工作時間；嚴禁代他人刷卡。如屬故意代刷，雙方均將被終止員工身分，因該行為視為對公司的舞弊。",
        "source_page": 4,
        "sort_order": 29
    },
    {
        "code": "21",
        "title": "第 21 條：遲到",
        "category": "attendance",
        "content_zh": "遲到 1 至 15 分鐘，累計 3 次者，發給 1 張警告單。遲到 30 分鐘以上者，將扣除其原可享有的福利，並須於 24 小時內完成請假單。",
        "source_page": 4,
        "sort_order": 30
    },
    {
        "code": "22",
        "title": "第 22 條：生產區域的行動電話、相機與通訊設備",
        "category": "workplace",
        "content_zh": "行動電話、相機及各類通訊設備，禁止帶入生產區域或公司指定區域；經個別授權者除外。如經查獲，視為嚴重違反紀律。",
        "source_page": 4,
        "sort_order": 31
    },
    {
        "code": "23",
        "title": "第 23 條：公開平台、公司資料、照片與生產資訊",
        "category": "discipline",
        "content_zh": "未經公司書面同意，無論是否出於故意，均不得在公開平台發布侮辱性文字，或揭露、散布公司的資料、照片、地點、產品、生產流程、設備、工具或機械等資訊；違者視為嚴重違反紀律。",
        "source_page": 4,
        "sort_order": 32
    },
    {
        "code": "24",
        "title": "第 24 條：工作時間使用行動電話與私人事務",
        "category": "workplace",
        "content_zh": "工作時間內禁止玩行動電話、傳送與工作無關的私人訊息，或處理私人事務；如因此降低工作效率或干擾他人工作，視為違反紀律。",
        "source_page": 4,
        "sort_order": 33
    },
    {
        "code": "25",
        "title": "第 25 條：公司電腦、設備、軟體與財產攜出",
        "category": "discipline",
        "content_zh": "公司提供的各類財產，包括桌上型電腦（PC）、筆記型電腦（Notebook）、iPad 及其他設備，僅供工作使用，不得用於娛樂；亦不得擅自改裝、增添或移除設備，或安裝、使用未經許可的軟體。上述行為視為嚴重違反紀律。將公司財產帶離工廠區域時，每次均須事先取得許可。",
        "source_page": 5,
        "sort_order": 34
    },
    {
        "code": "26",
        "title": "第 26 條：安全規章",
        "category": "discipline",
        "content_zh": "所有員工均須嚴格配合並遵守公司的安全規章。",
        "source_page": 5,
        "sort_order": 35
    },
    {
        "code": "BENEFITS",
        "title": "員工福利",
        "category": "benefits",
        "content_zh": "公司為員工提供的福利如下：\n\n1. 每月全勤獎金。\n2. 社會保險。\n3. 任職滿 1 年後，公司提供制服 1 件及鞋子 1 雙。\n4. 提供 1 格置物櫃，以確保個人物品安全。\n5. 每日午餐時段的餐費補助。\n6. 加班時段的餐費補助。\n7. 年度聯誼或聚餐活動及禮品。",
        "source_page": 5,
        "sort_order": 36
    },
    {
        "code": "CERTIFICATIONS",
        "title": "公司取得的認證標準",
        "category": "company",
        "content_zh": "公司已取得 ISO 13485 及 MDD 93/42/EEC 認證。",
        "source_page": 5,
        "sort_order": 37
    },
    {
        "code": "QUALITY_POLICY",
        "title": "公司品質政策",
        "category": "company",
        "content_zh": "- 品質符合需求\n- 準時交付\n- Emerald 持續致力於發展與改善\n- 因為客戶是最重要的人\n\n上述公司工作規章經審議後，認定內容適當。受僱人已詳盡閱讀並理解本規章，特此簽名作為重要證明。",
        "source_page": 5,
        "sort_order": 38
    }
]


def seed_work_rules(db: Session) -> dict:
    created = 0
    updated = 0
    for row in WORK_RULE_SEED:
        item = db.scalar(select(WorkRule).where(WorkRule.code == row["code"]))
        if item is None:
            item = WorkRule(**row)
            db.add(item)
            created += 1
            continue

        changed = False
        for field in ("title", "category", "content_zh", "source_page", "sort_order"):
            value = row[field]
            if getattr(item, field) != value:
                setattr(item, field, value)
                changed = True
        if item.source_document != "Emerald_工作規章_繁體中文譯本.pdf":
            item.source_document = "Emerald_工作規章_繁體中文譯本.pdf"
            changed = True
        if not item.active:
            item.active = True
            changed = True
        if changed:
            item.updated_at = datetime.now(timezone.utc)
            updated += 1

    db.commit()
    return {"created": created, "updated": updated, "total": len(WORK_RULE_SEED)}


ENTERPRISE_SOP_SEED = [
    ("ENT-001", "company", "all", "公司介紹與新人導航", "Company profile and new-starter navigation", "ข้อมูลบริษัทและเส้นทางพนักงานใหม่", "認識 Emerald、廠區、部門窗口與第一週必做事項；公開資料與內部規章清楚分開。", "Learn Emerald, the site, department contacts, and first-week actions, while separating public information from internal policy.", "ทำความรู้จัก Emerald สถานที่ ผู้ติดต่อ และสิ่งที่ต้องทำในสัปดาห์แรก โดยแยกข้อมูลสาธารณะจากระเบียบภายใน", "PUBLIC-1", "published", 1),
    ("SYS-001", "company", "all", "系統登入、語言與帳號安全", "System access, languages, and account security", "การเข้าใช้ระบบ ภาษา และความปลอดภัยบัญชี", "登入企業入口、切換繁中／英文／泰文並保護帳號。", "Sign in, switch Chinese/English/Thai, and protect account credentials.", "เข้าสู่ระบบ สลับภาษาจีน/อังกฤษ/ไทย และปกป้องบัญชี", "1.0", "published", 2),
    ("ATT-001", "attendance", "all", "打卡紀錄查詢與缺卡補登", "Attendance review and missed-punch correction", "ตรวจสอบเวลาและขอแก้ไขกรณีลืมลงเวลา", "查看上下班、遲到與缺卡；修正需填原因並保留稽核。", "Review clock records and request corrections with a reason and audit trail.", "ดูเวลาเข้าออกและขอแก้ไขพร้อมเหตุผลและบันทึกตรวจสอบ", "1.0", "published", 3),
    ("ROT-001", "attendance", "all", "A／B 組星期六輪班判斷", "A/B Saturday rotation calculation", "การคำนวณเวรวันเสาร์กลุ่ม A/B", "依基準日、個人組別、假日與特殊日判斷是否上班。", "Determine Saturday work from the anchor date, group, holidays, and overrides.", "ตรวจวันทำงานเสาร์จากวันฐาน กลุ่ม วันหยุด และวันพิเศษ", "1.0", "published", 4),
    ("LEV-001", "leave", "all", "請假申請、交接與審核", "Leave request, handover, and approval", "การลา การส่งมอบงาน และการอนุมัติ", "選擇假別與日期、確認實扣工作日、完成交接並送審。", "Select leave and dates, verify deductible workdays, complete handover, and submit for approval.", "เลือกประเภทและวันที่ ตรวจวันหักจริง ส่งมอบงาน และส่งอนุมัติ", "1.0", "published", 5),
    ("SAF-001", "safety", "all", "工廠安全、PPE 與危害通報", "Factory safety, PPE, and hazard reporting", "ความปลอดภัยโรงงาน PPE และการรายงานอันตราย", "待 HR／EHS 填入正式 PPE、禁區、事故與集合規定。", "Pending official PPE, restricted-area, incident, and assembly rules from HR/EHS.", "รอ HR/EHS เผยแพร่ข้อกำหนด PPE พื้นที่ห้ามเข้า เหตุการณ์ และจุดรวมพล", "HR-DRAFT", "draft", 6),
    ("QUA-001", "quality", "production", "生產區衛生、品質與不合格品", "Production hygiene, quality, and nonconforming product", "สุขอนามัยการผลิต คุณภาพ และสินค้าที่ไม่ผ่าน", "待 QA 確認進出、潔淨、隔離與不合格品流程。", "Pending QA confirmation for entry, cleanliness, isolation, and nonconforming product.", "รอ QA ยืนยันการเข้าออก ความสะอาด การแยก และสินค้าที่ไม่ผ่าน", "HR-DRAFT", "draft", 7),
    ("SEC-001", "security", "all", "保密、拍照、手機與資料處理", "Confidentiality, photography, phones, and data", "ความลับ การถ่ายภาพ โทรศัพท์ และข้อมูล", "待 HR／IT 確認拍照、個資、客戶資料與裝置規範。", "Pending HR/IT rules for photography, personal/customer data, and devices.", "รอ HR/IT ยืนยันการถ่ายภาพ ข้อมูลส่วนบุคคล/ลูกค้า และอุปกรณ์", "HR-DRAFT", "draft", 8),
    ("EMG-001", "emergency", "all", "火災、受傷、化學品與疏散", "Fire, injury, chemical event, and evacuation", "ไฟไหม้ บาดเจ็บ สารเคมี และการอพยพ", "待 EHS 填入警報、集合點、急救與通報程序。", "Pending EHS alarms, assembly points, first aid, and reporting procedures.", "รอ EHS เผยแพร่สัญญาณเตือน จุดรวมพล ปฐมพยาบาล และการรายงาน", "HR-DRAFT", "draft", 9),
    ("CON-001", "conduct", "all", "工作秩序、尊重與申訴", "Workplace order, respect, and grievance channels", "ระเบียบ ความเคารพ และช่องทางร้องเรียน", "待 HR 確認反騷擾、訪客、財物、整潔與申訴管道。", "Pending HR rules for anti-harassment, visitors, property, housekeeping, and grievances.", "รอ HR ยืนยันการต่อต้านการคุกคาม ผู้มาติดต่อ ทรัพย์สิน ความสะอาด และข้อร้องเรียน", "HR-DRAFT", "draft", 10),
]


def log_enterprise_event(
    db: Session, actor_id: str, action: str, resource: str = "", resource_id: str = "", detail: str = ""
) -> None:
    db.add(EnterpriseAuditEvent(actor_id=actor_id, action=action, resource=resource, resource_id=resource_id, detail=detail))


def seed_enterprise_data(db: Session) -> None:
    existing_codes = set(db.scalars(select(SOPDocument.code)))
    for code, category, role_scope, zh, en, th, s_zh, s_en, s_th, version, status_value, order in ENTERPRISE_SOP_SEED:
        if code in existing_codes:
            continue
        db.add(SOPDocument(
            code=code, category=category, role_scope=role_scope,
            title_zh=zh, title_en=en, title_th=th,
            summary_zh=s_zh, summary_en=s_en, summary_th=s_th,
            version=version, effective_date=date(2026, 1, 1) if status_value == "published" else None,
            status=status_value, required=True, sort_order=order,
        ))
    db.commit()

    if db.scalar(select(AttendanceRecord.id).limit(1)):
        return
    today = datetime.now(THAILAND_TZ).date()
    cursor = today.replace(day=1)
    patterns = [
        ("07:54", "17:05", "normal"), ("08:11", "17:02", "late"),
        ("07:58", "16:31", "early_leave"), (None, "17:08", "missing_punch"),
        ("07:52", "17:16", "normal"), ("07:57", "17:01", "normal"),
    ]
    index = 0
    while cursor <= today:
        if cursor.weekday() < 5:
            for employee_id in ("E001", "E002", "M001"):
                clock_in, clock_out, status_value = patterns[(index + len(employee_id)) % len(patterns)]
                db.add(AttendanceRecord(
                    employee_id=employee_id, work_date=cursor,
                    scheduled_start="08:00", scheduled_end="17:00",
                    clock_in=clock_in, clock_out=clock_out,
                    status=status_value, source="demo-seed",
                ))
            index += 1
        cursor += timedelta(days=1)
    db.commit()


def attendance_scope(stmt, user: User, db: Session, employee_id: str | None = None):
    if user.role == Role.employee.value:
        return stmt.where(AttendanceRecord.employee_id == user.id)
    if user.role == Role.manager.value:
        department_users = select(User.id).where(User.department == user.department)
        stmt = stmt.where(AttendanceRecord.employee_id.in_(department_users))
        if employee_id:
            allowed = db.scalar(select(User.id).where(User.id == employee_id, User.department == user.department))
            if not allowed:
                raise HTTPException(status_code=403, detail="Employee is outside your department")
            stmt = stmt.where(AttendanceRecord.employee_id == employee_id)
        return stmt
    if employee_id:
        stmt = stmt.where(AttendanceRecord.employee_id == employee_id)
    return stmt


def seed_demo_data() -> None:
    Base.metadata.create_all(engine)
    ensure_schema_compatibility()
    with SessionLocal() as db:
        get_rotation_schedule(db)
        users = [
            ("E001", "Wang", Role.employee.value, "Production", "A"),
            ("E002", "Chen", Role.employee.value, "Administration", "B"),
            ("M001", "Manager Lin", Role.manager.value, "Production", "B"),
            ("HR001", "HR Huang", Role.hr.value, "Administration", "NONE"),
            ("A001", "Administrator", Role.admin.value, "Administration", "NONE"),
        ]
        for user_id, name, role_value, department, rotation_group in users:
            if db.get(User, user_id) is None:
                db.add(User(
                    id=user_id, name=name, role=role_value, department=department,
                    rotation_group=rotation_group, password_hash=pwd_context.hash("1234"),
                ))
        db.commit()
        seed_enterprise_data(db)
        seed_work_rules(db)
        seed_onboarding_items(db)


app = FastAPI(
    title="Emerald Enterprise HR and SOP API",
    version="16.3.5-github-mysql-https",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://localhost:8080,http://127.0.0.1:8080",
    ).split(",")
    if origin.strip()
]

# Add Railway's generated HTTPS domain automatically when available.
railway_public_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").strip()
if railway_public_domain:
    railway_origin = f"https://{railway_public_domain}"
    if railway_origin not in origins:
        origins.append(railway_origin)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def rotate_default_passwords() -> None:
    """One-time-per-account cleanup: any user still on the seeded demo
    password ("1234") gets a fresh random password. Self-guarding - once an
    account is rotated, pwd_context.verify("1234", ...) will no longer match
    it, so re-running this on every startup is a cheap no-op for already
    rotated accounts. Gated behind ROTATE_DEFAULT_PASSWORDS so it only runs
    when explicitly requested, and the new passwords are printed to the
    deploy log exactly once (shown nowhere else - not stored in plaintext).
    """
    if os.getenv("ROTATE_DEFAULT_PASSWORDS", "").strip().lower() not in {"1", "true", "yes"}:
        return
    with SessionLocal() as db:
        rotated: list[tuple[str, str]] = []
        for user in db.scalars(select(User)):
            if pwd_context.verify("1234", user.password_hash):
                new_password = secrets.token_urlsafe(9)
                user.password_hash = pwd_context.hash(new_password)
                rotated.append((user.id, new_password))
        if rotated:
            db.commit()
            print("\n=== EMERALD: default passwords rotated (shown once, save now) ===")
            for user_id, new_password in rotated:
                print(f"{user_id}: {new_password}")
            print("=== end of rotated passwords ===\n")


def force_reset_all_passwords() -> None:
    """Admin-triggered bulk reset: sets a fresh random password for EVERY
    account regardless of its current password. Unlike rotate_default_passwords
    this is not self-guarding (it will re-run every startup while the env var
    is set), so it must be turned off again right after use. Gated behind
    FORCE_RESET_ALL_PASSWORDS; new passwords are printed to the deploy log
    exactly once (shown nowhere else - not stored in plaintext).
    """
    if os.getenv("FORCE_RESET_ALL_PASSWORDS", "").strip().lower() not in {"1", "true", "yes"}:
        return
    with SessionLocal() as db:
        reset: list[tuple[str, str]] = []
        for user in db.scalars(select(User)):
            new_password = secrets.token_urlsafe(9)
            user.password_hash = pwd_context.hash(new_password)
            reset.append((user.id, new_password))
        if reset:
            db.commit()
            print("\n=== EMERALD: ALL passwords force-reset (shown once, save now) ===")
            for user_id, new_password in reset:
                print(f"{user_id}: {new_password}")
            print("=== end of reset passwords ===\n")


@app.on_event("startup")
def startup() -> None:
    if SECRET_KEY == "change-this-before-production":
        print(
            "\n"
            "!!! SECURITY WARNING !!!\n"
            "EMERALD_SECRET is not set - using the default placeholder JWT signing key.\n"
            "Anyone who knows this default value could forge admin login tokens.\n"
            "Set a real random value in backend/.env before exposing this server\n"
            "beyond your own computer. See backend/.env.example.\n"
        )
    seed_demo_data()
    rotate_default_passwords()
    force_reset_all_passwords()
    bootstrap_calendar_years()
    start_holiday_scheduler()


@app.on_event("shutdown")
def shutdown() -> None:
    stop_holiday_scheduler()


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "emerald-enterprise-hr-api", "version": "16.3.5-github-mysql-https"}


_LOGIN_LOCKOUT_MAX_ATTEMPTS = int(os.getenv("LOGIN_LOCKOUT_MAX_ATTEMPTS", "5"))
_LOGIN_LOCKOUT_WINDOW_SECONDS = int(os.getenv("LOGIN_LOCKOUT_WINDOW_SECONDS", "300"))
_login_failures: dict[str, list[float]] = {}
_login_failures_lock = threading.Lock()


def _check_login_lockout(account: str) -> None:
    """Raise 429 if this account has failed too many times recently."""
    now = time.monotonic()
    with _login_failures_lock:
        attempts = [t for t in _login_failures.get(account, []) if now - t < _LOGIN_LOCKOUT_WINDOW_SECONDS]
        _login_failures[account] = attempts
        if len(attempts) >= _LOGIN_LOCKOUT_MAX_ATTEMPTS:
            retry_after = int(_LOGIN_LOCKOUT_WINDOW_SECONDS - (now - attempts[0]))
            raise HTTPException(
                status_code=429,
                detail=f"Too many failed login attempts. Try again in {max(retry_after, 1)} seconds.",
            )


def _record_login_failure(account: str) -> None:
    now = time.monotonic()
    with _login_failures_lock:
        _login_failures.setdefault(account, []).append(now)


def _clear_login_failures(account: str) -> None:
    with _login_failures_lock:
        _login_failures.pop(account, None)


_CHATBOT_RATE_LIMIT_PER_HOUR = int(os.getenv("CHATBOT_RATE_LIMIT_PER_HOUR", "30"))
_chatbot_requests: dict[str, list[float]] = {}
_chatbot_requests_lock = threading.Lock()


def _check_chatbot_rate_limit(user_id: str) -> None:
    """Raise 429 if this user has sent too many chat messages in the last hour.

    Protects against runaway LLM API costs (bugs, loops, or misuse) when a paid
    CHATBOT_API_KEY is configured. Adjust via CHATBOT_RATE_LIMIT_PER_HOUR.
    """
    now = time.monotonic()
    with _chatbot_requests_lock:
        recent = [t for t in _chatbot_requests.get(user_id, []) if now - t < 3600]
        recent.append(now)
        _chatbot_requests[user_id] = recent
        if len(recent) > _CHATBOT_RATE_LIMIT_PER_HOUR:
            raise HTTPException(
                status_code=429,
                detail=f"Too many AI questions this hour (limit: {_CHATBOT_RATE_LIMIT_PER_HOUR}). Please try again later.",
            )


@app.post("/api/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Annotated[Session, Depends(get_db)]) -> TokenResponse:
    account = payload.account.strip().upper()
    _check_login_lockout(account)
    user = db.get(User, account)
    if not user or not pwd_context.verify(payload.password, user.password_hash):
        _record_login_failure(account)
        raise HTTPException(status_code=401, detail="Invalid account or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="This account has been deactivated")
    _clear_login_failures(account)

    return TokenResponse(
        access_token=create_access_token(user.id, user.role),
        user={
            "id": user.id,
            "name": user.name,
            "role": user.role,
            "department": user.department,
            "rotation_group": user.rotation_group,
            "is_active": user.is_active,
            "photo_data": user.photo_data,
        },
    )


@app.post("/api/auth/token", response_model=TokenResponse)
def token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    return login(
        LoginRequest(
            account=form_data.username,
            password=form_data.password,
        ),
        db,
    )


@app.get("/api/admin/users", response_model=list[UserOut])
def list_users(
    _: Annotated[User, Depends(require_roles(Role.hr, Role.admin))],
    db: Annotated[Session, Depends(get_db)],
) -> list[User]:
    return list(db.scalars(select(User).order_by(User.id)))


@app.post(
    "/api/admin/users",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    payload: UserCreate,
    actor: Annotated[User, Depends(require_roles(Role.hr, Role.admin))],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    user_id = payload.id.strip().upper()
    name = payload.name.strip()
    department = payload.department.strip()

    if not user_id or not name or not department:
        raise HTTPException(
            status_code=422,
            detail="ID、姓名及部門不得空白",
        )

    if actor.role == Role.hr.value and payload.role in {Role.hr, Role.admin}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="HR 只能新增 employee 或 manager 角色的帳號，hr／admin 角色須由管理員建立",
        )

    if db.get(User, user_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists",
        )

    user = User(
        id=user_id,
        name=name,
        role=payload.role.value,
        department=department,
        rotation_group=payload.rotation_group,
        password_hash=pwd_context.hash(payload.password),
    )

    db.add(user)
    log_enterprise_event(
        db,
        actor.id,
        "user_created",
        "user",
        user_id,
        f"role={payload.role.value}; department={department}; rotation_group={payload.rotation_group}",
    )
    db.commit()
    db.refresh(user)

    return user

@app.post("/api/me/change-password")
def change_my_password(
    payload: PasswordChangeRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    if not pwd_context.verify(
        payload.current_password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="目前密碼不正確",
        )

    if payload.current_password == payload.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密碼不可與目前密碼相同",
        )

    user.password_hash = pwd_context.hash(payload.new_password)

    log_enterprise_event(
        db,
        user.id,
        "password_changed",
        "user",
        user.id,
        "User changed their own password",
    )

    db.commit()

    return {
        "message": "Password changed successfully",
        "user_id": user.id,
    }


@app.post("/api/admin/users/{user_id}/reset-password")
def admin_reset_user_password(
    user_id: str,
    payload: AdminPasswordResetRequest,
    actor: Annotated[User, Depends(require_roles(Role.hr, Role.admin))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    target_id = user_id.strip().upper()
    user = db.get(User, target_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if actor.role == Role.hr.value and user.role in {Role.hr.value, Role.admin.value}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="HR 不能重設 hr／admin 角色帳號的密碼，須由管理員操作",
        )

    user.password_hash = pwd_context.hash(payload.new_password)

    log_enterprise_event(
        db,
        actor.id,
        "admin_password_reset",
        "user",
        user.id,
        f"Password reset by administrator {actor.id}",
    )

    db.commit()

    return {
        "message": "Password reset successfully",
        "user_id": user.id,
    }


class UserStatusUpdate(BaseModel):
    is_active: bool


@app.patch("/api/admin/users/{user_id}/status", response_model=UserOut)
def admin_set_user_status(
    user_id: str,
    payload: UserStatusUpdate,
    actor: Annotated[User, Depends(require_roles(Role.hr, Role.admin))],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    target_id = user_id.strip().upper()
    user = db.get(User, target_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.id == actor.id and not payload.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate your own account",
        )

    if actor.role == Role.hr.value and user.role in {Role.hr.value, Role.admin.value}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="HR 不能停用／啟用 hr／admin 角色帳號，須由管理員操作",
        )

    user.is_active = payload.is_active
    log_enterprise_event(
        db,
        actor.id,
        "user_activated" if payload.is_active else "user_deactivated",
        "user",
        user.id,
        f"Account {'activated' if payload.is_active else 'deactivated'} by administrator {actor.id}",
    )
    db.commit()
    db.refresh(user)
    return user


class UserPhotoUpdate(BaseModel):
    photo_data: str | None = Field(default=None, max_length=60000)


@app.patch("/api/admin/users/{user_id}/photo", response_model=UserOut)
def admin_set_user_photo(
    user_id: str,
    payload: UserPhotoUpdate,
    actor: Annotated[User, Depends(require_roles(Role.hr, Role.admin))],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    target_id = user_id.strip().upper()
    user = db.get(User, target_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if payload.photo_data and not payload.photo_data.startswith("data:image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="photo_data must be a data:image/... URI",
        )

    user.photo_data = payload.photo_data
    log_enterprise_event(
        db,
        actor.id,
        "user_photo_updated" if payload.photo_data else "user_photo_removed",
        "user",
        user.id,
        f"Photo updated by {actor.id}",
    )
    db.commit()
    db.refresh(user)
    return user






@app.get("/api/onboarding/items", response_model=list[OnboardingItemOut])
def list_onboarding_items(
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[OnboardingItem]:
    stmt = (
        select(OnboardingItem)
        .where(OnboardingItem.active.is_(True))
        .order_by(OnboardingItem.sort_order, OnboardingItem.code)
    )
    return list(db.scalars(stmt))


@app.get("/api/onboarding/progress")
def get_onboarding_progress(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    rows = db.scalars(
        select(OnboardingProgress).where(OnboardingProgress.user_id == user.id)
    )
    return {row.item_id: row.completed for row in rows}


@app.post("/api/onboarding/progress/{item_id}")
def set_onboarding_progress(
    item_id: int,
    payload: OnboardingProgressUpdate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    item = db.get(OnboardingItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Onboarding item not found")

    row = db.scalar(
        select(OnboardingProgress).where(
            OnboardingProgress.user_id == user.id,
            OnboardingProgress.item_id == item_id,
        )
    )
    if not row:
        row = OnboardingProgress(user_id=user.id, item_id=item_id, completed=False)
        db.add(row)

    row.completed = payload.completed
    row.completed_at = datetime.now(timezone.utc) if payload.completed else None
    db.commit()
    return {"item_id": item_id, "completed": row.completed}


@app.get("/api/admin/onboarding-items", response_model=list[OnboardingItemOut])
def admin_list_onboarding_items(
    _: Annotated[User, Depends(require_roles(Role.hr, Role.admin))],
    db: Annotated[Session, Depends(get_db)],
) -> list[OnboardingItem]:
    stmt = select(OnboardingItem).order_by(OnboardingItem.sort_order, OnboardingItem.code)
    return list(db.scalars(stmt))


@app.post("/api/admin/onboarding-items", response_model=OnboardingItemOut, status_code=201)
def create_onboarding_item(
    payload: OnboardingItemCreate,
    actor: Annotated[User, Depends(require_roles(Role.hr, Role.admin))],
    db: Annotated[Session, Depends(get_db)],
) -> OnboardingItem:
    code = payload.code.strip().upper()
    if db.scalar(select(OnboardingItem).where(OnboardingItem.code == code)):
        raise HTTPException(status_code=409, detail="Onboarding item code already exists")

    item = OnboardingItem(
        code=code,
        title_zh=payload.title_zh.strip(),
        title_en=payload.title_en.strip(),
        title_th=payload.title_th.strip(),
        sort_order=payload.sort_order,
    )
    db.add(item)
    log_enterprise_event(db, actor.id, "onboarding_item_created", "onboarding_item", code, "")
    db.commit()
    db.refresh(item)
    return item


@app.put("/api/admin/onboarding-items/{item_id}", response_model=OnboardingItemOut)
def update_onboarding_item(
    item_id: int,
    payload: OnboardingItemUpdate,
    actor: Annotated[User, Depends(require_roles(Role.hr, Role.admin))],
    db: Annotated[Session, Depends(get_db)],
) -> OnboardingItem:
    item = db.get(OnboardingItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Onboarding item not found")

    for field in ("title_zh", "title_en", "title_th", "sort_order", "active"):
        value = getattr(payload, field)
        if value is not None:
            setattr(item, field, value.strip() if isinstance(value, str) else value)
    item.updated_at = datetime.now(timezone.utc)
    log_enterprise_event(db, actor.id, "onboarding_item_updated", "onboarding_item", item.code, "")
    db.commit()
    db.refresh(item)
    return item


@app.delete("/api/admin/onboarding-items/{item_id}")
def delete_onboarding_item(
    item_id: int,
    actor: Annotated[User, Depends(require_roles(Role.hr, Role.admin))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    item = db.get(OnboardingItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Onboarding item not found")
    item.active = False
    log_enterprise_event(db, actor.id, "onboarding_item_deleted", "onboarding_item", item.code, "")
    db.commit()
    return {"message": "Onboarding item deactivated", "code": item.code}


@app.get("/api/work-rules", response_model=list[WorkRuleOut])
def list_work_rules(
    category: str | None = None,
    _: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
) -> list[WorkRule]:
    stmt = (
        select(WorkRule)
        .where(WorkRule.active.is_(True))
        .order_by(WorkRule.sort_order, WorkRule.code)
    )
    if category:
        stmt = stmt.where(WorkRule.category == category.strip().lower())
    return list(db.scalars(stmt))


@app.get("/api/work-rules/search", response_model=list[WorkRuleOut])
def search_work_rules_sql(
    q: str = Query(min_length=1, max_length=200),
    limit: int = Query(default=20, ge=1, le=100),
    _: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
) -> list[WorkRule]:
    keyword = f"%{q.strip()}%"
    stmt = (
        select(WorkRule)
        .where(
            WorkRule.active.is_(True),
            or_(
                WorkRule.code.ilike(keyword),
                WorkRule.title.ilike(keyword),
                WorkRule.content_zh.ilike(keyword),
                WorkRule.category.ilike(keyword),
            ),
        )
        .order_by(WorkRule.sort_order, WorkRule.code)
        .limit(limit)
    )
    return list(db.scalars(stmt))


@app.get("/api/work-rules/{rule_code}", response_model=WorkRuleOut)
def get_work_rule(
    rule_code: str,
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> WorkRule:
    code = rule_code.strip().upper()
    item = db.scalar(
        select(WorkRule).where(
            WorkRule.code == code,
            WorkRule.active.is_(True),
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Work rule not found")
    return item


@app.post("/api/admin/work-rules", response_model=WorkRuleOut, status_code=201)
def create_work_rule(
    payload: WorkRuleCreate,
    actor: Annotated[User, Depends(require_roles(Role.hr, Role.admin))],
    db: Annotated[Session, Depends(get_db)],
) -> WorkRule:
    code = payload.code.strip()
    existing = db.scalar(select(WorkRule).where(WorkRule.code == code))
    if existing is not None:
        raise HTTPException(status_code=409, detail="A work rule with this code already exists")
    item = WorkRule(
        code=code,
        title=payload.title.strip(),
        category=payload.category.strip().lower(),
        content_zh=payload.content_zh.strip(),
        sort_order=payload.sort_order,
        source_document="Manually added via admin API",
        active=True,
    )
    db.add(item)
    log_enterprise_event(db, actor.id, "work_rule_created", "work_rule", code, payload.title)
    db.commit()
    db.refresh(item)
    return item


@app.put("/api/admin/work-rules/{rule_code}", response_model=WorkRuleOut)
def update_work_rule(
    rule_code: str,
    payload: WorkRuleUpdate,
    actor: Annotated[User, Depends(require_roles(Role.hr, Role.admin))],
    db: Annotated[Session, Depends(get_db)],
) -> WorkRule:
    item = db.scalar(select(WorkRule).where(WorkRule.code == rule_code.strip()))
    if item is None:
        raise HTTPException(status_code=404, detail="Work rule not found")
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        if field == "category" and value is not None:
            value = value.strip().lower()
        setattr(item, field, value)
    item.updated_at = datetime.now(timezone.utc)
    log_enterprise_event(db, actor.id, "work_rule_updated", "work_rule", item.code, str(updates))
    db.commit()
    db.refresh(item)
    return item


@app.delete("/api/admin/work-rules/{rule_code}", status_code=204, response_model=None)
def delete_work_rule(
    rule_code: str,
    actor: Annotated[User, Depends(require_roles(Role.hr, Role.admin))],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    item = db.scalar(select(WorkRule).where(WorkRule.code == rule_code.strip()))
    if item is None:
        raise HTTPException(status_code=404, detail="Work rule not found")
    item.active = False
    log_enterprise_event(db, actor.id, "work_rule_deactivated", "work_rule", item.code, "")
    db.commit()
    return None


@app.post("/api/admin/work-rules/reseed")
def reseed_work_rules(
    actor: Annotated[User, Depends(require_roles(Role.admin))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    result = seed_work_rules(db)
    log_enterprise_event(
        db,
        actor.id,
        "work_rules_reseeded",
        "work_rules",
        "all",
        f"created={{result['created']}}; updated={{result['updated']}}",
    )
    db.commit()
    return result


@app.get("/api/me")
def me(user: Annotated[User, Depends(get_current_user)]) -> dict:
    return {"id": user.id, "name": user.name, "role": user.role, "department": user.department, "rotation_group": user.rotation_group, "is_active": user.is_active, "photo_data": user.photo_data}


@app.get("/api/schedules/settings", response_model=RotationSettingsOut)
def rotation_settings(
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> RotationSchedule:
    return get_rotation_schedule(db)


@app.put("/api/schedules/settings", response_model=RotationSettingsOut)
def update_rotation_settings(
    payload: RotationSettingsUpdate,
    _: Annotated[User, Depends(require_roles(Role.hr, Role.admin))],
    db: Annotated[Session, Depends(get_db)],
) -> RotationSchedule:
    try:
        RotationSettingsData(
            anchor_date=payload.anchor_date,
            first_working_group=payload.first_working_group,
            cycle_weeks=payload.cycle_weeks,
            saturday_enabled=payload.saturday_enabled,
            sunday_is_day_off=payload.sunday_is_day_off,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    item = get_rotation_schedule(db)
    item.name = payload.name
    item.anchor_date = payload.anchor_date
    item.first_working_group = payload.first_working_group
    item.cycle_weeks = payload.cycle_weeks
    item.saturday_enabled = payload.saturday_enabled
    item.sunday_is_day_off = payload.sunday_is_day_off
    item.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(item)
    return item


@app.patch("/api/users/{user_id}/rotation-group")
def update_user_rotation_group(
    user_id: str,
    payload: RotationGroupUpdate,
    _: Annotated[User, Depends(require_roles(Role.hr, Role.admin))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    item = db.get(User, user_id.upper())
    if not item:
        raise HTTPException(status_code=404, detail="User not found")
    item.rotation_group = payload.rotation_group
    db.commit()
    return {
        "id": item.id,
        "name": item.name,
        "department": item.department,
        "rotation_group": item.rotation_group,
    }


@app.get("/api/schedules/me")
def my_schedule_for_date(
    target_date: date = Query(alias="date"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    schedule = get_rotation_schedule(db)
    overrides = get_calendar_overrides(db, target_date, target_date)
    holidays = holiday_dates_between(db, target_date, target_date)
    result = classify_workday(
        target_date=target_date,
        rotation_group=user.rotation_group,
        settings=_rotation_settings_data(schedule),
        holidays=holidays,
        overrides=_override_data(overrides),
    )
    result["employee_id"] = user.id
    return result


@app.get("/api/schedules/upcoming-saturdays")
def my_upcoming_saturdays(
    start: date | None = None,
    count: int = Query(default=12, ge=1, le=52),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    start_date = start or datetime.now(THAILAND_TZ).date()
    end_date = start_date + timedelta(days=count * 7 + 7)
    schedule = get_rotation_schedule(db)
    overrides = get_calendar_overrides(db, start_date, end_date)
    holidays = holiday_dates_between(db, start_date, end_date)
    return {
        "employee_id": user.id,
        "rotation_group": user.rotation_group,
        "items": upcoming_saturdays(
            start_date=start_date,
            count=count,
            rotation_group=user.rotation_group,
            settings=_rotation_settings_data(schedule),
            holidays=holidays,
            overrides=_override_data(overrides),
        ),
    }


@app.post("/api/leaves/calculate")
def calculate_leave_endpoint(
    payload: LeaveCalculateRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    if payload.end_date < payload.start_date:
        raise HTTPException(status_code=422, detail="End date cannot precede start date")
    return calculate_user_leave(db, user, payload.start_date, payload.end_date)


@app.get("/api/schedules/overrides", response_model=list[CalendarOverrideOut])
def list_calendar_overrides(
    year: int | None = None,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CalendarOverride]:
    start_date = date(year, 1, 1) if year else None
    end_date = date(year, 12, 31) if year else None
    return get_calendar_overrides(db, start_date, end_date)


@app.post("/api/schedules/overrides", response_model=CalendarOverrideOut, status_code=201)
def create_calendar_override(
    payload: CalendarOverrideCreate,
    _: User = Depends(require_roles(Role.hr, Role.admin)),
    db: Session = Depends(get_db),
) -> CalendarOverride:
    existing = db.scalar(
        select(CalendarOverride).where(
            CalendarOverride.date == payload.date,
            CalendarOverride.rotation_group == payload.rotation_group,
        )
    )
    item = existing or CalendarOverride(
        date=payload.date,
        rotation_group=payload.rotation_group,
        override_type=payload.override_type,
        note=payload.note,
    )
    item.override_type = payload.override_type
    item.note = payload.note
    if existing is None:
        db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.delete("/api/schedules/overrides/{override_id}")
def delete_calendar_override(
    override_id: int,
    _: User = Depends(require_roles(Role.hr, Role.admin)),
    db: Session = Depends(get_db),
) -> dict:
    item = db.get(CalendarOverride, override_id)
    if not item:
        raise HTTPException(status_code=404, detail="Calendar override not found")
    db.delete(item)
    db.commit()
    return {"deleted": override_id}


def _detect_message_language(message: str, fallback: str = "zh-TW") -> str:
    text = str(message or "").strip()
    if any("\u0e00" <= char <= "\u0e7f" for char in text):
        return "th"
    if any(("\u3400" <= char <= "\u4dbf") or ("\u4e00" <= char <= "\u9fff") for char in text):
        return "zh-TW"
    if any(char.isascii() and char.isalpha() for char in text):
        return "en"
    return fallback if fallback in {"zh-TW", "en", "th"} else "zh-TW"


def _utility_chat_answer(message: str, language: str) -> dict | None:
    lowered = " ".join(message.lower().strip().split())
    plain = lowered.strip("!?？！，。,.")
    greeting_words = {"你好", "您好", "哈囉", "哈啰", "嗨", "hello", "hi", "hey", "สวัสดี", "หวัดดี"}
    if plain in greeting_words:
        messages = {
            "zh-TW": "你好！我是 Emerald 請假助理。你可以詢問請假規章、病假證明、審核流程、泰國假日、星期六輪休，以及目前日期或時間。",
            "en": "Hello! I am the Emerald leave assistant. You can ask about leave policies, medical certificates, approval workflows, Thai holidays, Saturday rotations, or the current date and time.",
            "th": "สวัสดี ฉันคือผู้ช่วยการลาของ Emerald คุณสามารถถามเรื่องระเบียบการลา ใบรับรองแพทย์ ขั้นตอนอนุมัติ วันหยุดไทย ตารางเวรวันเสาร์ หรือวันและเวลาปัจจุบันได้",
        }
        return {
            "answer": messages.get(language, messages["zh-TW"]),
            "sources": [],
            "mode": "greeting-tool",
        }

    time_keywords = [
        "現在幾點", "现在几点", "幾點了", "几点了", "現在時間", "现在时间",
        "what time is it", "current time", "time now",
        "ตอนนี้กี่โมง", "กี่โมงแล้ว", "เวลาเท่าไหร่",
    ]
    date_keywords = [
        "今天幾號", "今天几号", "今天日期", "現在日期", "现在日期",
        "what date is it", "today's date", "current date",
        "วันนี้วันที่เท่าไหร่", "วันนี้วันอะไร",
    ]
    wants_time = any(keyword in lowered for keyword in time_keywords)
    wants_date = any(keyword in lowered for keyword in date_keywords)
    if not wants_time and not wants_date:
        return None

    now = datetime.now(THAILAND_TZ)
    date_text = now.strftime("%Y-%m-%d")
    time_text = now.strftime("%H:%M:%S")
    weekday_zh = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][now.weekday()]
    weekday_en = now.strftime("%A")
    weekday_th = ["วันจันทร์", "วันอังคาร", "วันพุธ", "วันพฤหัสบดี", "วันศุกร์", "วันเสาร์", "วันอาทิตย์"][now.weekday()]

    if wants_time and wants_date:
        messages = {
            "zh-TW": f"現在是泰國時間 {date_text} {weekday_zh} {time_text}。",
            "en": f"It is {time_text} on {weekday_en}, {date_text}, in Thailand (Asia/Bangkok).",
            "th": f"ขณะนี้เวลา {time_text} น. วันที่ {date_text} {weekday_th} ตามเวลาไทย",
        }
    elif wants_date:
        messages = {
            "zh-TW": f"今天是泰國日期 {date_text}，{weekday_zh}。",
            "en": f"Today is {weekday_en}, {date_text}, in Thailand (Asia/Bangkok).",
            "th": f"วันนี้คือวันที่ {date_text} {weekday_th} ตามเวลาไทย",
        }
    else:
        messages = {
            "zh-TW": f"現在是泰國時間 {time_text}。",
            "en": f"The current time in Thailand (Asia/Bangkok) is {time_text}.",
            "th": f"ขณะนี้เวลา {time_text} น. ตามเวลาไทย",
        }

    return {
        "answer": messages.get(language, messages["zh-TW"]),
        "sources": [],
        "mode": "time-tool",
        "timezone": "Asia/Bangkok",
        "timestamp": now.isoformat(timespec="seconds"),
    }


def _schedule_chat_target(message: str) -> date | None:
    lowered = message.lower()
    keywords = [
        "輪休", "星期六", "週六", "周六", "上班嗎", "work saturday",
        "saturday shift", "rotation", "วันเสาร์", "ทำงานวันเสาร์", "ตารางเวร",
    ]
    if not any(keyword in lowered for keyword in keywords):
        return None
    today = datetime.now(THAILAND_TZ).date()
    days_until = (5 - today.weekday()) % 7
    target = today + timedelta(days=days_until)
    next_keywords = ["下週", "下周", "next saturday", "เสาร์หน้า", "สัปดาห์หน้า"]
    if any(keyword in lowered for keyword in next_keywords):
        target += timedelta(days=7)
    return target


def _char_ngrams(text: str, n: int = 2) -> set[str]:
    compact = re.sub(r"\s+", "", text.lower())
    if len(compact) < n:
        return {compact} if compact else set()
    return {compact[i:i + n] for i in range(len(compact) - n + 1)}


_WORK_RULES_TRIGGER_WORDS = (
    "規章", "规章", "條款", "条款", "第", "條", "条", "病假", "事假", "年假", "特休",
    "離職", "离职", "試用期", "试用期", "遲到", "迟到", "曠職", "旷职", "加班",
    "警告", "打卡", "刷卡", "制服", "識別證", "识别证", "手機", "手机", "行動電話",
    "武器", "飲酒", "饮酒", "毒品", "賭博", "赌博", "吸菸", "吸烟", "醫療證明",
    "医疗证明", "福利", "工作規則", "工作规则", "work rule", "rule", "policy",
    "regulation", "ระเบียบ", "กฎ",
)

# Common HR terms in English / Thai mapped to the Chinese vocabulary actually used
# in the work-rules text. The n-gram matcher only understands Chinese characters,
# so a non-Chinese question needs these Chinese terms injected before matching,
# otherwise every English/Thai question falls through to the generic (and much
# less accurate) document search.
_WORK_RULES_SYNONYMS: tuple[tuple[str, str], ...] = (
    ("sick leave", "病假"), ("medical certificate", "醫療證明"), ("doctor's note", "醫療證明"),
    ("personal leave", "事假"), ("annual leave", "年假"), ("vacation", "年假"),
    ("resign", "離職"), ("resignation", "離職"), ("notice period", "離職通知"), ("quit", "離職"),
    ("probation", "試用期"), ("probationary period", "試用期"),
    ("late", "遲到"), ("tardy", "遲到"), ("tardiness", "遲到"),
    ("absent without", "曠職"), ("absence", "曠職"),
    ("overtime", "加班"), ("ot ", "加班"),
    ("warning", "警告"), ("disciplinary", "警告 違規"),
    ("clock in", "打卡"), ("time card", "刷卡"), ("punch card", "刷卡"),
    ("uniform", "制服"), ("id badge", "識別證"), ("identification card", "識別證"),
    ("mobile phone", "行動電話 手機"), ("cell phone", "行動電話 手機"), ("smartphone", "行動電話 手機"),
    ("weapon", "武器"), ("alcohol", "飲酒"), ("drink", "飲酒"), ("drug", "毒品"),
    ("gambling", "賭博"), ("smoking", "吸菸"), ("cigarette", "吸菸"),
    ("benefit", "福利"), ("bonus", "全勤獎金"), ("military service", "兵役"),
    ("company property", "公司財產"), ("laptop", "筆記型電腦"), ("computer", "電腦"),
    ("confidential", "洩漏公司資料"), ("harassment", "申訴"), ("fight", "鬥毆"),
    ("ลาป่วย", "病假"), ("ใบรับรองแพทย์", "醫療證明"), ("ลากิจ", "事假"),
    ("ลาพักร้อน", "年假"), ("ลาออก", "離職"), ("ทดลองงาน", "試用期"),
    ("มาสาย", "遲到"), ("ขาดงาน", "曠職"), ("ล่วงเวลา", "加班"),
    ("ตักเตือน", "警告"), ("ตอกบัตร", "打卡"), ("เครื่องแบบ", "制服"),
    ("บัตรพนักงาน", "識別證"), ("โทรศัพท์มือถือ", "行動電話 手機"), ("อาวุธ", "武器"),
    ("แอลกอฮอล์", "飲酒"), ("ยาเสพติด", "毒品"), ("การพนัน", "賭博"), ("สูบบุหรี่", "吸菸"),
    ("สวัสดิการ", "福利"), ("ทหาร", "兵役"),
)


def _cjk_only(text: str) -> str:
    return "".join(char for char in text if "\u3400" <= char <= "\u9fff")


def _augment_query_with_synonyms(text: str) -> str:
    lowered = text.lower()
    extra_terms = [zh for en_th, zh in _WORK_RULES_SYNONYMS if en_th in lowered]
    return f"{text} {' '.join(extra_terms)}" if extra_terms else text


def _work_rules_chat_answer(message: str, language: str, db: Session) -> dict | None:
    stripped = message.strip()
    if not stripped:
        return None
    augmented = _augment_query_with_synonyms(stripped)
    lowered = augmented.lower()
    if not any(word.lower() in lowered for word in _WORK_RULES_TRIGGER_WORDS):
        return None

    rules = list(db.scalars(select(WorkRule).where(WorkRule.active.is_(True))))
    if not rules:
        return None

    query_grams = _char_ngrams(_cjk_only(augmented), 3) | _char_ngrams(_cjk_only(augmented), 2)
    if not query_grams:
        return None
    query_compact = re.sub(r"\s+", "", augmented.lower())

    rule_gram_sets: dict[str, set[str]] = {}
    for rule in rules:
        haystack = f"{rule.title} {rule.content_zh} {rule.category}"
        rule_gram_sets[rule.code] = _char_ngrams(haystack, 3) | _char_ngrams(haystack, 2)

    # IDF-style weighting: a gram shared by almost every rule (e.g. "天", "通知")
    # carries little discriminating value; a gram unique to one or two rules does.
    gram_doc_count: dict[str, int] = {}
    for grams in rule_gram_sets.values():
        for gram in grams:
            gram_doc_count[gram] = gram_doc_count.get(gram, 0) + 1
    total_rules = max(1, len(rule_gram_sets))

    scored: list[tuple[float, WorkRule]] = []
    for rule in rules:
        rule_grams = rule_gram_sets.get(rule.code, set())
        if not rule_grams:
            continue
        shared = query_grams & rule_grams
        weighted = sum(
            1.0 / gram_doc_count.get(gram, total_rules) for gram in shared
        )
        overlap = weighted / len(query_grams)
        # Strong signal: the rule's own title words appear directly in the question.
        title_words = [w for w in re.split(r"[^\w]+", rule.title) if len(w) >= 2]
        title_boost = 0.5 if any(w.lower() in query_compact for w in title_words) else 0.0
        score = overlap + title_boost
        if score > 0:
            scored.append((score, rule))

    if not scored:
        return None
    scored.sort(key=lambda pair: pair[0], reverse=True)
    top_score, best_rule = scored[0]
    if top_score < 0.05:
        return None

    runner_ups = [rule for score, rule in scored[1:3] if score >= top_score * 0.6]

    header = {
        "zh-TW": f"根據公司工作規章第 {best_rule.code} 條（{best_rule.title}）：",
        "en": f"Per the company work rules, Article {best_rule.code} ({best_rule.title}):",
        "th": f"ตามระเบียบข้อบังคับบริษัท ข้อ {best_rule.code} ({best_rule.title}):",
    }.get(language, f"根據公司工作規章第 {best_rule.code} 條（{best_rule.title}）：")

    answer = f"{header}\n{best_rule.content_zh}"
    if language != "zh-TW":
        language_name = {"en": "English", "th": "Thai"}.get(language, language)
        translated = None
        try:
            translated = _call_chat_completion(
                [
                    {
                        "role": "system",
                        "content": (
                            f"Translate the following official company work-rule text into {language_name}. "
                            "This is a legal/HR policy document: preserve every number, date, time, deadline, "
                            "and named institution or role exactly as given, do not summarize or omit anything. "
                            "Reply with ONLY the translated text, no quotes, no explanation."
                        ),
                    },
                    {"role": "user", "content": best_rule.content_zh},
                ],
                temperature=0,
            )
        except (httpx.HTTPError, RuntimeError, ValueError) as exc:
            print(f"[work_rules] Translation skipped (provider error): {exc}")

        if translated:
            translated_note = {
                "en": "\n\n(Machine-translated from the Chinese original; the Chinese text is the authoritative version.)",
                "th": "\n\n(แปลด้วยระบบอัตโนมัติจากต้นฉบับภาษาจีน หากมีข้อสงสัยให้ยึดตามต้นฉบับภาษาจีนเป็นหลัก)",
            }.get(language, "")
            answer = f"{header}\n{translated}{translated_note}"
        elif language == "th":
            # No translation provider configured. Rather than show the Chinese
            # text with a "Chinese only" disclaimer, defer to the RAG pipeline,
            # which has a properly written native-Thai source document
            # (emerald_work_rules_thai_original.md) that answers Thai questions
            # directly without needing machine translation.
            return None
        else:
            note = {
                "en": "\n\n(Note: the official rule text above is in Chinese only; ask HR for a translated copy if needed.)",
                "th": "\n\n(หมายเหตุ: ข้อความระเบียบด้านบนเป็นภาษาจีนเท่านั้น กรุณาสอบถาม HR หากต้องการฉบับแปล)",
            }.get(language)
            if note:
                answer += note
    if runner_ups:
        related = "、".join(f"第 {r.code} 條" for r in runner_ups)
        suffix = {
            "zh-TW": f"\n\n（也可能相關：{related}）",
            "en": f"\n\n(Possibly related: {related})",
            "th": f"\n\n(อาจเกี่ยวข้อง: {related})",
        }.get(language, f"\n\n（也可能相關：{related}）")
        answer += suffix

    return {
        "answer": answer,
        "sources": [
            {"title": f"工作規章第 {best_rule.code} 條", "source": "work_rules_sql", "date": None}
        ],
        "mode": "work-rules-sql",
        "matches": [
            {"code": best_rule.code, "title": best_rule.title, "score": round(top_score, 4)}
        ],
    }


def _schedule_chat_answer(message: str, language: str, user: User, db: Session) -> dict | None:
    target = _schedule_chat_target(message)
    if target is None:
        return None
    schedule = get_rotation_schedule(db)
    overrides = get_calendar_overrides(db, target, target)
    holidays = holiday_dates_between(db, target, target)
    result = classify_workday(
        target_date=target,
        rotation_group=user.rotation_group,
        settings=_rotation_settings_data(schedule),
        holidays=holidays,
        overrides=_override_data(overrides),
    )
    yes = bool(result["is_workday"])
    working_group = result.get("working_group") or "—"
    messages = {
        "zh-TW": (
            f"{target.isoformat()} 是星期六。你的輪休組別是 {user.rotation_group} 組；"
            f"當天排定上班組別是 {working_group} 組。"
            f"因此你{'需要上班' if yes else '輪休，不需要上班'}。"
        ),
        "en": (
            f"{target.isoformat()} is a Saturday. Your rotation group is {user.rotation_group}; "
            f"the scheduled working group is {working_group}. "
            f"You {'are scheduled to work' if yes else 'are off under the rotation schedule'}."
        ),
        "th": (
            f"วันที่ {target.isoformat()} เป็นวันเสาร์ กลุ่มเวรของคุณคือ {user.rotation_group} "
            f"และกลุ่มที่ทำงานในวันนั้นคือ {working_group} ดังนั้นคุณ"
            f"{'ต้องมาทำงาน' if yes else 'เป็นวันหยุดตามรอบเวร'}"
        ),
    }
    return {
        "answer": messages.get(language, messages["zh-TW"]),
        "sources": [
            {
                "title": "Personal Saturday rotation schedule",
                "source": "schedule-database",
                "date": target.isoformat(),
            }
        ],
        "mode": "schedule-tool",
        "schedule": result,
    }


@app.get("/api/sops", response_model=list[SOPOut])
def list_sops(
    status_filter: str | None = Query(default=None, alias="status"),
    category: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SOPDocument]:
    stmt = select(SOPDocument).order_by(SOPDocument.sort_order, SOPDocument.code)
    if status_filter:
        stmt = stmt.where(SOPDocument.status == status_filter)
    if category:
        stmt = stmt.where(SOPDocument.category == category)
    items = list(db.scalars(stmt))
    if user.role in {Role.hr.value, Role.admin.value}:
        return items
    department = user.department.lower()
    return [
        item for item in items
        if "all" in {scope.strip().lower() for scope in item.role_scope.split(",")}
        or user.role in {scope.strip().lower() for scope in item.role_scope.split(",")}
        or department in {scope.strip().lower() for scope in item.role_scope.split(",")}
    ]


@app.get("/api/sops/progress")
def sop_progress(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    published = list(db.scalars(select(SOPDocument).where(SOPDocument.status == "published", SOPDocument.required.is_(True))))
    acknowledgements = list(db.scalars(select(SOPAcknowledgement).where(SOPAcknowledgement.user_id == user.id)))
    acknowledged_ids = {item.sop_id for item in acknowledgements}
    total = len(published)
    done = sum(1 for item in published if item.id in acknowledged_ids)
    return {
        "employee_id": user.id,
        "required_total": total,
        "completed": done,
        "percent": round(done / total * 100) if total else 100,
        "acknowledgements": [
            {"sop_id": item.sop_id, "version": item.version, "quiz_score": item.quiz_score, "acknowledged_at": item.acknowledged_at}
            for item in acknowledgements
        ],
    }


@app.post("/api/sops/{sop_id}/acknowledge", status_code=201)
def acknowledge_sop(
    sop_id: int,
    payload: SOPAcknowledgementCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    item = db.get(SOPDocument, sop_id)
    if not item:
        raise HTTPException(status_code=404, detail="SOP not found")
    if item.status != "published":
        raise HTTPException(status_code=409, detail="Only published SOPs can be acknowledged")
    if payload.quiz_score < payload.passing_score:
        raise HTTPException(
            status_code=422,
            detail=f"A quiz score of at least {payload.passing_score} is required",
        )
    acknowledgement = db.scalar(select(SOPAcknowledgement).where(
        SOPAcknowledgement.user_id == user.id,
        SOPAcknowledgement.sop_id == item.id,
        SOPAcknowledgement.version == item.version,
    ))
    if acknowledgement is None:
        acknowledgement = SOPAcknowledgement(
            user_id=user.id, sop_id=item.id, version=item.version, quiz_score=payload.quiz_score
        )
        db.add(acknowledgement)
    else:
        acknowledgement.quiz_score = max(acknowledgement.quiz_score, payload.quiz_score)
        acknowledgement.acknowledged_at = datetime.now(timezone.utc)
    log_enterprise_event(db, user.id, "sop_acknowledged", "sop", str(item.id), f"{item.code} v{item.version}")
    db.commit()
    db.refresh(acknowledgement)
    return {
        "id": acknowledgement.id,
        "sop_id": item.id,
        "code": item.code,
        "version": acknowledgement.version,
        "quiz_score": acknowledgement.quiz_score,
        "acknowledged_at": acknowledgement.acknowledged_at,
    }


@app.post("/api/admin/sops", response_model=SOPOut, status_code=201)
def create_sop(
    payload: SOPCreate,
    actor: Annotated[User, Depends(require_roles(Role.hr, Role.admin))],
    db: Annotated[Session, Depends(get_db)],
) -> SOPDocument:
    code = payload.code.strip()
    existing = db.scalar(select(SOPDocument).where(SOPDocument.code == code))
    if existing is not None:
        raise HTTPException(status_code=409, detail="A SOP with this code already exists")
    item = SOPDocument(
        code=code,
        category=payload.category.strip().lower(),
        role_scope=payload.role_scope.strip() or "all",
        title_zh=payload.title_zh.strip(),
        title_en=payload.title_en.strip(),
        title_th=payload.title_th.strip(),
        summary_zh=payload.summary_zh.strip(),
        summary_en=payload.summary_en.strip(),
        summary_th=payload.summary_th.strip(),
        version=payload.version.strip(),
        effective_date=date.today() if payload.status == "published" else None,
        status=payload.status,
        required=payload.required,
        sort_order=payload.sort_order,
    )
    db.add(item)
    log_enterprise_event(db, actor.id, "sop_created", "sop", code, payload.title_zh)
    db.commit()
    db.refresh(item)
    return item


@app.put("/api/admin/sops/{sop_id}", response_model=SOPOut)
def update_sop(
    sop_id: int,
    payload: SOPUpdate,
    actor: Annotated[User, Depends(require_roles(Role.hr, Role.admin))],
    db: Annotated[Session, Depends(get_db)],
) -> SOPDocument:
    item = db.get(SOPDocument, sop_id)
    if item is None:
        raise HTTPException(status_code=404, detail="SOP not found")
    updates = payload.model_dump(exclude_unset=True)
    became_published = updates.get("status") == "published" and item.status != "published"
    for field, value in updates.items():
        if field == "category" and value is not None:
            value = value.strip().lower()
        setattr(item, field, value)
    if became_published and item.effective_date is None:
        item.effective_date = date.today()
    item.updated_at = datetime.now(timezone.utc)
    log_enterprise_event(db, actor.id, "sop_updated", "sop", item.code, str(updates))
    db.commit()
    db.refresh(item)
    return item


@app.delete("/api/admin/sops/{sop_id}", status_code=204, response_model=None)
def delete_sop(
    sop_id: int,
    actor: Annotated[User, Depends(require_roles(Role.hr, Role.admin))],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    item = db.get(SOPDocument, sop_id)
    if item is None:
        raise HTTPException(status_code=404, detail="SOP not found")
    backup = {
        "code": item.code, "category": item.category, "role_scope": item.role_scope,
        "title_zh": item.title_zh, "title_en": item.title_en, "title_th": item.title_th,
        "summary_zh": item.summary_zh, "summary_en": item.summary_en, "summary_th": item.summary_th,
        "version": item.version, "status": item.status, "required": item.required,
        "sort_order": item.sort_order,
    }
    log_enterprise_event(
        db, actor.id, "sop_deleted", "sop", item.code,
        f"BACKUP (use POST /api/admin/sops to restore): {json.dumps(backup, ensure_ascii=False)}",
    )
    db.delete(item)
    db.commit()
    return None


@app.get("/api/attendance", response_model=list[AttendanceOut])
def list_attendance(
    start_date: date | None = None,
    end_date: date | None = None,
    employee_id: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AttendanceRecord]:
    today = datetime.now(THAILAND_TZ).date()
    start_value = start_date or today.replace(day=1)
    end_value = end_date or today
    stmt = select(AttendanceRecord).where(
        AttendanceRecord.work_date >= start_value,
        AttendanceRecord.work_date <= end_value,
    ).order_by(AttendanceRecord.work_date.desc(), AttendanceRecord.employee_id)
    stmt = attendance_scope(stmt, user, db, employee_id.upper() if employee_id else None)
    return list(db.scalars(stmt))


@app.get("/api/attendance/summary")
def attendance_summary(
    start_date: date | None = None,
    end_date: date | None = None,
    employee_id: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    records = list_attendance(start_date, end_date, employee_id, user, db)
    total = len(records)
    normal = sum(item.status == "normal" for item in records)
    return {
        "total_records": total,
        "normal": normal,
        "late": sum(item.status == "late" for item in records),
        "early_leave": sum(item.status == "early_leave" for item in records),
        "missing_punch": sum(item.status == "missing_punch" for item in records),
        "absent": sum(item.status == "absent" for item in records),
        "normal_rate": round(normal / total * 100) if total else 100,
    }


@app.post("/api/attendance/import")
def import_attendance(
    payload: AttendanceImportRequest,
    user: User = Depends(require_roles(Role.hr, Role.admin)),
    db: Session = Depends(get_db),
) -> dict:
    inserted = 0
    updated = 0
    for record in payload.records:
        employee_id = record.employee_id.upper()
        if db.get(User, employee_id) is None:
            raise HTTPException(status_code=422, detail=f"Unknown employee: {employee_id}")
        item = db.scalar(select(AttendanceRecord).where(
            AttendanceRecord.employee_id == employee_id,
            AttendanceRecord.work_date == record.work_date,
        ))
        if item is None:
            item = AttendanceRecord(employee_id=employee_id, work_date=record.work_date)
            db.add(item)
            inserted += 1
        else:
            updated += 1
        item.scheduled_start = record.scheduled_start
        item.scheduled_end = record.scheduled_end
        item.clock_in = record.clock_in
        item.clock_out = record.clock_out
        item.status = record.status
        item.source = record.source
        item.note = record.note
        item.updated_at = datetime.now(timezone.utc)
    log_enterprise_event(db, user.id, "attendance_import", "attendance", "batch", f"records={len(payload.records)}")
    db.commit()
    return {"inserted": inserted, "updated": updated, "total": len(payload.records)}


@app.post("/api/attendance/{attendance_id}/corrections", response_model=AttendanceCorrectionOut, status_code=201)
def create_attendance_correction(
    attendance_id: int,
    payload: AttendanceCorrectionCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AttendanceCorrection:
    record = db.get(AttendanceRecord, attendance_id)
    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    if user.role == Role.employee.value and record.employee_id != user.id:
        raise HTTPException(status_code=403, detail="You can only correct your own attendance")
    if user.role == Role.manager.value:
        employee = db.get(User, record.employee_id)
        if not employee or employee.department != user.department:
            raise HTTPException(status_code=403, detail="Employee is outside your department")
    item = AttendanceCorrection(
        attendance_id=record.id, employee_id=record.employee_id,
        requested_clock_in=payload.requested_clock_in,
        requested_clock_out=payload.requested_clock_out,
        reason=payload.reason, status="pending",
    )
    db.add(item)
    log_enterprise_event(db, user.id, "attendance_correction_requested", "attendance", str(record.id), payload.reason)
    db.commit()
    db.refresh(item)
    return item


@app.get("/api/attendance/corrections", response_model=list[AttendanceCorrectionOut])
def list_attendance_corrections(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AttendanceCorrection]:
    stmt = select(AttendanceCorrection).order_by(AttendanceCorrection.created_at.desc())
    if user.role == Role.employee.value:
        stmt = stmt.where(AttendanceCorrection.employee_id == user.id)
    elif user.role == Role.manager.value:
        department_users = select(User.id).where(User.department == user.department)
        stmt = stmt.where(AttendanceCorrection.employee_id.in_(department_users))
    return list(db.scalars(stmt))


@app.post("/api/attendance/corrections/{correction_id}/review", response_model=AttendanceCorrectionOut)
def review_attendance_correction(
    correction_id: int,
    payload: AttendanceCorrectionReview,
    user: User = Depends(require_roles(Role.manager, Role.hr, Role.admin)),
    db: Session = Depends(get_db),
) -> AttendanceCorrection:
    item = db.get(AttendanceCorrection, correction_id)
    if not item:
        raise HTTPException(status_code=404, detail="Correction request not found")
    if item.status != "pending":
        raise HTTPException(status_code=409, detail="Correction request was already reviewed")
    record = db.get(AttendanceRecord, item.attendance_id)
    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    if user.role == Role.manager.value:
        employee = db.get(User, record.employee_id)
        if not employee or employee.department != user.department:
            raise HTTPException(status_code=403, detail="Employee is outside your department")
    item.status = payload.status
    item.reviewed_by = user.id
    item.review_note = payload.review_note
    item.reviewed_at = datetime.now(timezone.utc)
    if payload.status == "approved":
        if item.requested_clock_in is not None:
            record.clock_in = item.requested_clock_in
        if item.requested_clock_out is not None:
            record.clock_out = item.requested_clock_out
        record.status = "normal" if record.clock_in and record.clock_out else "missing_punch"
        record.note = f"Corrected through request {item.id}"
        record.updated_at = datetime.now(timezone.utc)
    log_enterprise_event(db, user.id, f"attendance_correction_{payload.status}", "attendance_correction", str(item.id), payload.review_note)
    db.commit()
    db.refresh(item)
    return item


@app.get("/api/enterprise/audit")
def enterprise_audit(
    limit: int = Query(default=100, ge=1, le=500),
    _: User = Depends(require_roles(Role.hr, Role.admin)),
    db: Session = Depends(get_db),
) -> list[dict]:
    items = list(db.scalars(select(EnterpriseAuditEvent).order_by(EnterpriseAuditEvent.id.desc()).limit(limit)))
    return [
        {"id": item.id, "actor_id": item.actor_id, "action": item.action, "resource": item.resource,
         "resource_id": item.resource_id, "detail": item.detail, "created_at": item.created_at}
        for item in items
    ]


@app.post("/api/rag/search")
def rag_search(
    payload: RagSearchRequest,
    _: Annotated[User, Depends(get_current_user)],
) -> dict:
    try:
        return search_knowledge(payload.question, top_k=payload.top_k)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail="RAG index is not available. Run: python -m rag.build_index",
        ) from exc


@app.post("/api/rag/chat")
def rag_chat(
    payload: RagChatRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    _check_chatbot_rate_limit(user.id)
    response_language = _detect_message_language(payload.message, payload.language)
    utility_answer = _utility_chat_answer(payload.message, response_language)
    if utility_answer is not None:
        return utility_answer
    schedule_answer = _schedule_chat_answer(payload.message, response_language, user, db)
    if schedule_answer is not None:
        return schedule_answer
    work_rules_answer = _work_rules_chat_answer(payload.message, response_language, db)
    if work_rules_answer is not None:
        return work_rules_answer
    try:
        return chat_knowledge(
            payload.message,
            history=[item.model_dump() for item in payload.history],
            top_k=payload.top_k,
            language=response_language,
            user_context={"id": user.id, "role": user.role},
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail="RAG index is not available. Run: python -m rag.build_index",
        ) from exc


@app.get("/api/leaves", response_model=list[LeaveOut])
def list_leaves(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[LeaveRequest]:
    stmt = select(LeaveRequest).order_by(LeaveRequest.id.desc())
    if user.role == Role.employee.value:
        stmt = stmt.where(LeaveRequest.employee_id == user.id)
    elif user.role == Role.manager.value:
        dept_employee_ids = select(User.id).where(User.department == user.department)
        stmt = stmt.where(LeaveRequest.employee_id.in_(dept_employee_ids))
    return list(db.scalars(stmt))


@app.post("/api/leaves", response_model=LeaveOut, status_code=201)
def create_leave(
    payload: LeaveCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> LeaveRequest:
    if payload.end_date < payload.start_date:
        raise HTTPException(status_code=422, detail="End date cannot precede start date")

    calculation = calculate_user_leave(db, user, payload.start_date, payload.end_date)
    if calculation["workdays"] <= 0:
        raise HTTPException(status_code=422, detail="The selected period contains no working days")

    item = LeaveRequest(
        employee_id=user.id,
        leave_type=payload.leave_type,
        start_date=payload.start_date,
        end_date=payload.end_date,
        reason=payload.reason,
        workdays=calculation["workdays"],
        status=LeaveStatus.manager_pending.value,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.post("/api/leaves/{leave_id}/manager-approve", response_model=LeaveOut)
def manager_approve(
    leave_id: int,
    user: Annotated[User, Depends(require_roles(Role.manager, Role.admin))],
    db: Annotated[Session, Depends(get_db)],
) -> LeaveRequest:
    item = db.get(LeaveRequest, leave_id)
    if not item:
        raise HTTPException(status_code=404, detail="Leave request not found")
    if item.status != LeaveStatus.manager_pending.value:
        raise HTTPException(status_code=409, detail="Request is not awaiting manager approval")
    if user.role == Role.manager.value:
        employee = db.get(User, item.employee_id)
        if not employee or employee.department != user.department:
            raise HTTPException(status_code=403, detail="Employee is outside your department")
    item.status = LeaveStatus.hr_pending.value
    db.commit()
    db.refresh(item)
    return item


@app.post("/api/leaves/{leave_id}/hr-approve", response_model=LeaveOut)
def hr_approve(
    leave_id: int,
    _: Annotated[User, Depends(require_roles(Role.hr, Role.admin))],
    db: Annotated[Session, Depends(get_db)],
) -> LeaveRequest:
    item = db.get(LeaveRequest, leave_id)
    if not item:
        raise HTTPException(status_code=404, detail="Leave request not found")
    if item.status != LeaveStatus.hr_pending.value:
        raise HTTPException(status_code=409, detail="Request is not awaiting HR approval")
    item.status = LeaveStatus.approved.value
    db.commit()
    db.refresh(item)
    return item


@app.post("/api/leaves/{leave_id}/reject", response_model=LeaveOut)
def reject_leave(
    leave_id: int,
    user: Annotated[User, Depends(require_roles(Role.manager, Role.hr, Role.admin))],
    db: Annotated[Session, Depends(get_db)],
) -> LeaveRequest:
    item = db.get(LeaveRequest, leave_id)
    if not item:
        raise HTTPException(status_code=404, detail="Leave request not found")
    if user.role == Role.manager.value:
        employee = db.get(User, item.employee_id)
        if not employee or employee.department != user.department:
            raise HTTPException(status_code=403, detail="Employee is outside your department")
    item.status = LeaveStatus.rejected.value
    db.commit()
    db.refresh(item)
    return item


@app.get("/api/holidays", response_model=list[HolidayOut])
def list_holidays(
    year: int | None = None,
    country: str = "TH",
    confirmed_only: bool = False,
    db: Session = Depends(get_db),
) -> list[Holiday]:
    target_year = year or datetime.now(timezone.utc).year
    ensure_year_exists(db, target_year, country.upper())
    stmt = (
        select(Holiday)
        .where(Holiday.country == country.upper(), Holiday.year == target_year)
        .order_by(Holiday.date)
    )
    if confirmed_only:
        stmt = stmt.where(Holiday.company_confirmed.is_(True))
    return list(db.scalars(stmt))


@app.get("/api/holidays/sync-status")
def holiday_sync_status() -> dict:
    with _holiday_sync_state_guard:
        state = dict(_holiday_sync_state)
    state.update(
        {
            "enabled": HOLIDAY_AUTO_SYNC_ENABLED,
            "timezone": "Asia/Bangkok",
            "daily_time": f"{HOLIDAY_AUTO_SYNC_HOUR:02d}:{HOLIDAY_AUTO_SYNC_MINUTE:02d}",
            "next_run_at": (
                _iso_bangkok(_next_holiday_sync_at())
                if HOLIDAY_AUTO_SYNC_ENABLED
                else None
            ),
        }
    )
    return state


@app.post("/api/holidays/initialize/{year}")
def initialize_holiday_year(
    year: int,
    country: str = "TH",
    _: User = Depends(require_roles(Role.hr, Role.admin)),
    db: Session = Depends(get_db),
) -> dict:
    if year < 2020 or year > 2100:
        raise HTTPException(status_code=422, detail="Unsupported year")
    created = ensure_year_exists(db, year, country.upper())
    return {
        "year": year,
        "country": country.upper(),
        "created": created,
        "message": "Year initialized. HR review is required before company confirmation.",
    }


@app.post("/api/holidays", response_model=HolidayOut, status_code=201)
def create_company_holiday(
    payload: HolidayCreate,
    _: User = Depends(require_roles(Role.hr, Role.admin)),
    db: Session = Depends(get_db),
) -> Holiday:
    item = Holiday(
        country=payload.country.upper(),
        year=payload.date.year,
        date=payload.date.date(),
        name=payload.name,
        holiday_type=payload.holiday_type,
        company_confirmed=payload.company_confirmed,
        source="manual",
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.patch("/api/holidays/{holiday_id}/confirm", response_model=HolidayOut)
def confirm_holiday(
    holiday_id: int,
    payload: HolidayConfirmRequest,
    _: User = Depends(require_roles(Role.hr, Role.admin)),
    db: Session = Depends(get_db),
) -> Holiday:
    item = db.get(Holiday, holiday_id)
    if not item:
        raise HTTPException(status_code=404, detail="Holiday not found")
    item.company_confirmed = payload.company_confirmed
    db.commit()
    db.refresh(item)
    return item


@app.post("/api/holidays/sync/{year}")
def sync_holiday_year_endpoint(
    year: int,
    country: str = "TH",
    _: User = Depends(require_roles(Role.hr, Role.admin)),
    db: Session = Depends(get_db),
) -> dict:
    if year < 2020 or year > 2100:
        raise HTTPException(status_code=422, detail="Unsupported year")
    if country.upper() != "TH":
        raise HTTPException(status_code=422, detail="Automatic sync currently supports TH only")
    try:
        return sync_holiday_year(db, year, country)
    except HolidaySourceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/api/holidays/auto-sync")
def auto_sync_holidays(
    _: None = Depends(require_holiday_sync_key),
    db: Session = Depends(get_db),
) -> dict:
    return execute_holiday_auto_sync("api_key", db)


@app.post("/api/holidays/annual-rollover")
def annual_rollover(
    _: User = Depends(require_roles(Role.hr, Role.admin)),
    db: Session = Depends(get_db),
) -> dict:
    result = execute_holiday_auto_sync("hr_manual", db)
    result["note"] = (
        "Source dates were synchronized when available. HR confirmation is preserved "
        "and remains required for company holidays."
    )
    return result

# ---------------------------------------------------------------------------
# Full-stack web serving
# ---------------------------------------------------------------------------
# On Railway the Docker image places the frontend at /app/frontend.
# During local source execution it lives at <repository>/frontend.
_frontend_candidates = [
    Path(__file__).resolve().parent.parent / "frontend",
    Path(__file__).resolve().parents[2] / "frontend",
]
FRONTEND_DIR = next((path for path in _frontend_candidates if path.is_dir()), None)

if FRONTEND_DIR is not None:
    # Mounted last so all /api routes and /api/docs continue to take priority.
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
else:
    print("WARNING: frontend directory not found; API-only mode enabled.")

