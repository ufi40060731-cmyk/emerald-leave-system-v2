from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterable, Mapping

VALID_ROTATION_GROUPS = {"A", "B", "NONE"}
VALID_OVERRIDE_TYPES = {"WORKDAY", "DAY_OFF"}


@dataclass(frozen=True)
class RotationSettingsData:
    anchor_date: date
    first_working_group: str = "A"
    cycle_weeks: int = 2
    saturday_enabled: bool = True
    sunday_is_day_off: bool = True

    def __post_init__(self) -> None:
        first_group = self.first_working_group.upper()
        if first_group not in {"A", "B"}:
            raise ValueError("first_working_group must be A or B")
        if self.cycle_weeks < 2:
            raise ValueError("cycle_weeks must be at least 2")
        if self.anchor_date.weekday() != 5:
            raise ValueError("anchor_date must be a Saturday")


@dataclass(frozen=True)
class CalendarOverrideData:
    target_date: date
    override_type: str
    rotation_group: str = "ALL"
    note: str = ""

    def __post_init__(self) -> None:
        kind = self.override_type.upper()
        group = self.rotation_group.upper()
        if kind not in VALID_OVERRIDE_TYPES:
            raise ValueError("override_type must be WORKDAY or DAY_OFF")
        if group not in {"ALL", "A", "B", "NONE"}:
            raise ValueError("rotation_group must be ALL, A, B, or NONE")


def normalized_group(value: str | None) -> str:
    group = str(value or "NONE").strip().upper()
    return group if group in VALID_ROTATION_GROUPS else "NONE"


def saturday_working_group(target_date: date, settings: RotationSettingsData) -> str | None:
    """Return the group scheduled to work on the target Saturday.

    The anchor Saturday is assigned to ``first_working_group``. Subsequent Saturdays
    alternate A/B. ``cycle_weeks`` is accepted for future expansion, but the current
    implementation intentionally enforces the common two-team alternating pattern.
    """

    if target_date.weekday() != 5 or not settings.saturday_enabled:
        return None
    weeks = (target_date - settings.anchor_date).days // 7
    first = settings.first_working_group.upper()
    if weeks % 2 == 0:
        return first
    return "B" if first == "A" else "A"


def _matching_override(
    target_date: date,
    rotation_group: str,
    overrides: Iterable[CalendarOverrideData],
) -> CalendarOverrideData | None:
    group = normalized_group(rotation_group)
    specific: CalendarOverrideData | None = None
    global_override: CalendarOverrideData | None = None
    for item in overrides:
        if item.target_date != target_date:
            continue
        override_group = item.rotation_group.upper()
        if override_group == group:
            specific = item
        elif override_group == "ALL":
            global_override = item
    return specific or global_override


def classify_workday(
    target_date: date,
    rotation_group: str,
    settings: RotationSettingsData,
    holidays: set[date] | None = None,
    overrides: Iterable[CalendarOverrideData] = (),
) -> dict:
    """Classify one calendar date for leave deduction.

    Company overrides take priority. Then official/company holidays, Sunday, the
    rotating Saturday rule, and finally ordinary Monday-Friday workdays are applied.
    """

    group = normalized_group(rotation_group)
    holiday_dates = holidays or set()
    override = _matching_override(target_date, group, overrides)
    if override:
        is_workday = override.override_type.upper() == "WORKDAY"
        return {
            "date": target_date.isoformat(),
            "is_workday": is_workday,
            "category": "override_workday" if is_workday else "override_day_off",
            "rotation_group": group,
            "working_group": saturday_working_group(target_date, settings),
            "note": override.note,
        }

    if target_date in holiday_dates:
        return {
            "date": target_date.isoformat(),
            "is_workday": False,
            "category": "holiday",
            "rotation_group": group,
            "working_group": saturday_working_group(target_date, settings),
            "note": "",
        }

    weekday = target_date.weekday()
    if weekday == 6 and settings.sunday_is_day_off:
        return {
            "date": target_date.isoformat(),
            "is_workday": False,
            "category": "sunday",
            "rotation_group": group,
            "working_group": None,
            "note": "",
        }

    if weekday == 5:
        if not settings.saturday_enabled:
            return {
                "date": target_date.isoformat(),
                "is_workday": False,
                "category": "saturday_day_off",
                "rotation_group": group,
                "working_group": None,
                "note": "",
            }
        working_group = saturday_working_group(target_date, settings)
        is_workday = group in {"A", "B"} and group == working_group
        return {
            "date": target_date.isoformat(),
            "is_workday": is_workday,
            "category": "rotation_workday" if is_workday else "rotation_day_off",
            "rotation_group": group,
            "working_group": working_group,
            "note": "",
        }

    return {
        "date": target_date.isoformat(),
        "is_workday": True,
        "category": "weekday",
        "rotation_group": group,
        "working_group": None,
        "note": "",
    }


def calculate_leave_days(
    start_date: date,
    end_date: date,
    rotation_group: str,
    settings: RotationSettingsData,
    holidays: set[date] | None = None,
    overrides: Iterable[CalendarOverrideData] = (),
) -> dict:
    if end_date < start_date:
        raise ValueError("end_date cannot precede start_date")

    details: list[dict] = []
    current = start_date
    while current <= end_date:
        details.append(
            classify_workday(
                current,
                rotation_group=rotation_group,
                settings=settings,
                holidays=holidays,
                overrides=overrides,
            )
        )
        current += timedelta(days=1)

    category_counts: dict[str, int] = {}
    for item in details:
        category = str(item["category"])
        category_counts[category] = category_counts.get(category, 0) + 1

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "rotation_group": normalized_group(rotation_group),
        "calendar_days": len(details),
        "workdays": sum(1 for item in details if item["is_workday"]),
        "holidays": category_counts.get("holiday", 0),
        "sundays": category_counts.get("sunday", 0),
        "rotation_days_off": category_counts.get("rotation_day_off", 0),
        "rotation_workdays": category_counts.get("rotation_workday", 0),
        "override_days_off": category_counts.get("override_day_off", 0),
        "override_workdays": category_counts.get("override_workday", 0),
        "details": details,
    }


def upcoming_saturdays(
    start_date: date,
    count: int,
    rotation_group: str,
    settings: RotationSettingsData,
    holidays: set[date] | None = None,
    overrides: Iterable[CalendarOverrideData] = (),
) -> list[dict]:
    current = start_date
    while current.weekday() != 5:
        current += timedelta(days=1)
    rows: list[dict] = []
    for _ in range(max(count, 0)):
        rows.append(
            classify_workday(
                current,
                rotation_group=rotation_group,
                settings=settings,
                holidays=holidays,
                overrides=overrides,
            )
        )
        current += timedelta(days=7)
    return rows


def overrides_from_mapping(items: Mapping[date, tuple[str, str, str]]) -> list[CalendarOverrideData]:
    return [
        CalendarOverrideData(target_date=key, override_type=value[0], rotation_group=value[1], note=value[2])
        for key, value in items.items()
    ]
