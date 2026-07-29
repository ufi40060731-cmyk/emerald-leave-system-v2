#!/usr/bin/env python3
"""Generate GitHub Pages holiday JSON for the current and next Thai year."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.holiday_sync import (  # noqa: E402
    HolidaySourceError,
    fetch_holiday_html,
    localized_holiday_names,
    parse_holiday_html,
)

OUTPUT_DIR = ROOT / "frontend" / "data" / "holidays"
TIMEZONE = ZoneInfo("Asia/Bangkok")


def _read_existing(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None
    return data if isinstance(data, dict) else None


def _holiday_rows(year: int) -> tuple[list[dict], str]:
    html, source_url = fetch_holiday_html(year)
    candidates = parse_holiday_html(html, year)
    rows = [
        {
            "date": item.date.isoformat(),
            "name": item.name,
            "names": localized_holiday_names(item.name, item.date),
            "holiday_type": "official",
            "company_confirmed": False,
            "source": "holidays-calendar.net",
        }
        for item in candidates
    ]
    return rows, source_url


def update_year(year: int) -> bool:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{year}.json"
    existing = _read_existing(path)

    try:
        rows, source_url = _holiday_rows(year)
    except HolidaySourceError as exc:
        if existing and existing.get("holidays"):
            print(f"{year}: source unavailable; keeping existing JSON ({exc})")
            return False
        print(f"{year}: no published data yet ({exc})")
        return False

    core = {
        "country": "TH",
        "year": year,
        "source": "holidays-calendar.net",
        "source_url": source_url,
        "holidays": rows,
    }
    existing_core = None
    if existing:
        existing_core = {key: existing.get(key) for key in core}

    if existing_core == core:
        print(f"{year}: unchanged ({len(rows)} holidays)")
        return False

    payload = {
        **core,
        "updated_at": datetime.now(TIMEZONE).isoformat(timespec="seconds"),
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"{year}: updated {path.relative_to(ROOT)} ({len(rows)} holidays)")
    return True


def main() -> int:
    current_year = datetime.now(TIMEZONE).year
    changed = False
    for year in (current_year, current_year + 1):
        changed = update_year(year) or changed
    print("Static holiday data changed." if changed else "No static holiday changes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
