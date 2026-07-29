#!/usr/bin/env python3
"""Validate GitHub Pages Thailand holiday JSON files before deployment."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOLIDAY_DIR = ROOT / "frontend" / "data" / "holidays"
LANGUAGES = {"zh-TW", "en", "th"}


def validate_file(path: Path) -> int:
    payload = json.loads(path.read_text(encoding="utf-8"))
    year = int(payload["year"])
    if payload.get("country") != "TH":
        raise ValueError(f"{path}: country must be TH")
    if path.stem != str(year):
        raise ValueError(f"{path}: filename and payload year do not match")

    holidays = payload.get("holidays")
    if not isinstance(holidays, list) or not holidays:
        raise ValueError(f"{path}: holidays must be a non-empty list")

    seen: set[tuple[str, str]] = set()
    for index, item in enumerate(holidays):
        holiday_date = date.fromisoformat(item["date"])
        if holiday_date.year != year:
            raise ValueError(f"{path}: item {index} is outside {year}")
        name = str(item.get("name", "")).strip()
        if not name:
            raise ValueError(f"{path}: item {index} has no canonical name")
        names = item.get("names")
        if not isinstance(names, dict) or not LANGUAGES.issubset(names):
            raise ValueError(f"{path}: item {index} must contain zh-TW, en, and th names")
        if any(not str(names[language]).strip() for language in LANGUAGES):
            raise ValueError(f"{path}: item {index} has an empty localized name")
        key = (item["date"], name)
        if key in seen:
            raise ValueError(f"{path}: duplicate holiday {key}")
        seen.add(key)

    return len(holidays)


def main() -> int:
    files = sorted(HOLIDAY_DIR.glob("*.json"))
    if not files:
        raise SystemExit("No holiday JSON files found.")
    total = sum(validate_file(path) for path in files)
    print(f"Holiday JSON validation passed: {len(files)} file(s), {total} holiday row(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
