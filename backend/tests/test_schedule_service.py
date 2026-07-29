from datetime import date

from app.schedule_service import (
    CalendarOverrideData,
    RotationSettingsData,
    calculate_leave_days,
    classify_workday,
    saturday_working_group,
)


SETTINGS = RotationSettingsData(
    anchor_date=date(2026, 1, 3),
    first_working_group="A",
    cycle_weeks=2,
    saturday_enabled=True,
    sunday_is_day_off=True,
)


def test_alternating_saturday_groups():
    assert saturday_working_group(date(2026, 1, 3), SETTINGS) == "A"
    assert saturday_working_group(date(2026, 1, 10), SETTINGS) == "B"
    assert saturday_working_group(date(2026, 1, 17), SETTINGS) == "A"


def test_group_a_rotation_day_off():
    result = classify_workday(date(2026, 1, 10), "A", SETTINGS)
    assert result["is_workday"] is False
    assert result["category"] == "rotation_day_off"
    assert result["working_group"] == "B"


def test_leave_calculation_excludes_rotation_day_and_sunday():
    result = calculate_leave_days(
        date(2026, 1, 9),
        date(2026, 1, 12),
        "A",
        SETTINGS,
    )
    assert result["calendar_days"] == 4
    assert result["workdays"] == 2
    assert result["rotation_days_off"] == 1
    assert result["sundays"] == 1


def test_company_override_can_force_workday():
    override = CalendarOverrideData(
        target_date=date(2026, 1, 10),
        override_type="WORKDAY",
        rotation_group="A",
        note="Inventory count",
    )
    result = classify_workday(date(2026, 1, 10), "A", SETTINGS, overrides=[override])
    assert result["is_workday"] is True
    assert result["category"] == "override_workday"
