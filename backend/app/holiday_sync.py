from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from html.parser import HTMLParser
from zoneinfo import ZoneInfo

import httpx


SOURCE_NAME = "holidays-calendar.net"
CURRENT_YEAR_URL = "https://holidays-calendar.net/calendar_zh_tw/thailand_zh_tw.html"
ARCHIVE_URL_TEMPLATE = (
    "https://holidays-calendar.net/{year}/calendar_zh_tw/thailand_zh_tw.html"
)


class HolidaySourceError(RuntimeError):
    """Raised when the external holiday page cannot be safely imported."""


@dataclass(frozen=True)
class HolidayCandidate:
    date: date
    name: str


@dataclass
class _RawEntry:
    month: int
    day: int
    end_month: int | None
    end_day: int | None
    is_substitute: bool
    fragments: list[str]


class _TextTokenParser(HTMLParser):
    """Extract visible text nodes while ignoring scripts and styles."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tokens: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[no-untyped-def]
        if tag in {"script", "style", "noscript"}:
            self._ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._ignored_depth:
            return
        token = re.sub(r"\s+", " ", data).strip()
        if token:
            self.tokens.append(token)


_DATE_RE = re.compile(
    r"^\s*"
    r"(?:(?P<month>\d{1,2})月)?"
    r"(?P<day>\d{1,2})日"
    r"(?:\s*[–—－\-至~～]\s*"
    r"(?:(?P<end_month>\d{1,2})月)?"
    r"(?P<end_day>\d{1,2})日?"
    r")?"
    r"(?P<substitute>補假)?"
    r"\s*(?P<rest>.*)$"
)

_DESCRIPTION_PREFIXES = (
    "慶祝",
    "紀念",
    "佛教節日",
    "泰國的",
    "泰曆",
    "現任",
    "國王與",
    "國際勞動節",
    "政府部門",
    "僅限",
    "因舉辦",
    "參考",
)


_FIXED_DATE_ZH_TW_NAMES = {
    (1, 1): "公曆新年",
    (4, 6): "恰克里王朝開國紀念日",
    (5, 1): "勞動節",
    (5, 4): "泰王登基紀念日",
    (6, 3): "蘇提達王后誕辰日",
    (7, 28): "國王瓦吉拉隆功誕辰日",
    (8, 12): "詩麗吉王太后誕辰日（母親節）",
    (10, 13): "拉瑪九世國王逝世紀念日",
    (10, 23): "朱拉隆功大帝紀念日",
    (12, 5): "拉瑪九世國王普密蓬·阿杜德誕辰紀念日（父親節）",
    (12, 10): "泰國憲法紀念日",
    (12, 31): "元旦前夕",
}

_HOLIDAY_TRANSLATIONS = {
    "公曆新年": {
        "zh-TW": "公曆新年",
        "en": "New Year's Day",
        "th": "วันขึ้นปีใหม่",
    },
    "特別假期": {
        "zh-TW": "特別假期",
        "en": "Special holiday",
        "th": "วันหยุดพิเศษ",
    },
    "萬佛節": {
        "zh-TW": "萬佛節",
        "en": "Makha Bucha Day",
        "th": "วันมาฆบูชา",
    },
    "恰克里王朝開國紀念日": {
        "zh-TW": "恰克里王朝開國紀念日",
        "en": "Chakri Memorial Day",
        "th": "วันจักรี",
    },
    "宋干節（潑水節）": {
        "zh-TW": "宋干節（潑水節）",
        "en": "Songkran Festival",
        "th": "วันสงกรานต์",
    },
    "勞動節": {
        "zh-TW": "勞動節",
        "en": "National Labour Day",
        "th": "วันแรงงานแห่งชาติ",
    },
    "泰王登基紀念日": {
        "zh-TW": "泰王登基紀念日",
        "en": "Coronation Day",
        "th": "วันฉัตรมงคล",
    },
    "春耕節": {
        "zh-TW": "春耕節",
        "en": "Royal Ploughing Ceremony Day",
        "th": "วันพืชมงคล",
    },
    "佛誕節": {
        "zh-TW": "佛誕節",
        "en": "Visakha Bucha Day",
        "th": "วันวิสาขบูชา",
    },
    "蘇提達王后誕辰日": {
        "zh-TW": "蘇提達王后誕辰日",
        "en": "Queen Suthida's Birthday",
        "th": "วันเฉลิมพระชนมพรรษาสมเด็จพระนางเจ้าสุทิดาฯ",
    },
    "國王瓦吉拉隆功誕辰日": {
        "zh-TW": "國王瓦吉拉隆功誕辰日",
        "en": "King Vajiralongkorn's Birthday",
        "th": "วันเฉลิมพระชนมพรรษาพระบาทสมเด็จพระเจ้าอยู่หัว",
    },
    "三寶佛節": {
        "zh-TW": "三寶佛節",
        "en": "Asarnha Bucha Day",
        "th": "วันอาสาฬหบูชา",
    },
    "守夏節": {
        "zh-TW": "守夏節",
        "en": "Buddhist Lent Day",
        "th": "วันเข้าพรรษา",
    },
    "詩麗吉王太后誕辰日（母親節）": {
        "zh-TW": "詩麗吉王太后誕辰日（母親節）",
        "en": "Queen Sirikit The Queen Mother's Birthday (Mother's Day)",
        "th": "วันเฉลิมพระชนมพรรษาสมเด็จพระบรมราชชนนีพันปีหลวง (วันแม่แห่งชาติ)",
    },
    "拉瑪九世國王逝世紀念日": {
        "zh-TW": "拉瑪九世國王逝世紀念日",
        "en": "King Bhumibol Memorial Day",
        "th": "วันนวมินทรมหาราช",
    },
    "朱拉隆功大帝紀念日": {
        "zh-TW": "朱拉隆功大帝紀念日",
        "en": "Chulalongkorn Day",
        "th": "วันปิยมหาราช",
    },
    "拉瑪九世國王普密蓬·阿杜德誕辰紀念日（父親節）": {
        "zh-TW": "拉瑪九世國王普密蓬·阿杜德誕辰紀念日（父親節）",
        "en": "King Bhumibol's Birthday Memorial (Father's Day)",
        "th": "วันคล้ายวันพระบรมราชสมภพรัชกาลที่ 9 (วันพ่อแห่งชาติ)",
    },
    "拉瑪九世誕辰日（父親節）": {
        "zh-TW": "拉瑪九世誕辰日（父親節）",
        "en": "King Bhumibol's Birthday Memorial (Father's Day)",
        "th": "วันคล้ายวันพระบรมราชสมภพรัชกาลที่ 9 (วันพ่อแห่งชาติ)",
    },
    "泰國憲法紀念日": {
        "zh-TW": "泰國憲法紀念日",
        "en": "Constitution Day",
        "th": "วันรัฐธรรมนูญ",
    },
    "憲法紀念日": {
        "zh-TW": "泰國憲法紀念日",
        "en": "Constitution Day",
        "th": "วันรัฐธรรมนูญ",
    },
    "元旦前夕": {
        "zh-TW": "元旦前夕",
        "en": "New Year's Eve",
        "th": "วันสิ้นปี",
    },
}

_LOCALIZED_SUFFIXES = {
    "substitute": {
        "zh-TW": "（補假）",
        "en": " (substitute holiday)",
        "th": " (วันหยุดชดเชย)",
    },
    "bangkok_only": {
        "zh-TW": "（僅曼谷）",
        "en": " (Bangkok only)",
        "th": " (เฉพาะกรุงเทพฯ)",
    },
}


def normalize_holiday_name(name: str, holiday_date: date) -> str:
    """Return a clean Traditional Chinese label for calendar display.

    The upstream zh-TW page occasionally mixes English text or inconsistent
    transliterations into otherwise Chinese labels. Fixed-date national
    holidays are normalized to stable Traditional Chinese names; other labels
    keep their source wording with English-only parentheses removed.
    """

    normalized = re.sub(r"\s+", " ", name).strip()
    fixed_name = _FIXED_DATE_ZH_TW_NAMES.get((holiday_date.month, holiday_date.day))
    if fixed_name:
        if "補假" in normalized and "補假" not in fixed_name:
            return f"{fixed_name}（補假）"
        return fixed_name

    normalized = re.sub(
        r"[（(][^）)]*[A-Za-z][^）)]*[）)]",
        "",
        normalized,
    )
    normalized = re.sub(r"\s+", " ", normalized).strip(" ：:、-—")
    return normalized


def localized_holiday_names(name: str, holiday_date: date) -> dict[str, str]:
    """Return stable Traditional Chinese, English, and Thai holiday labels.

    The source page is Traditional Chinese. Known Thailand public holidays are
    translated locally so GitHub Pages never depends on a translation service.
    Unknown future labels remain visible in Chinese rather than being discarded.
    """

    normalized = normalize_holiday_name(name, holiday_date)
    suffixes: list[str] = []
    suffix_patterns = (
        ("（補假）", "substitute"),
        ("(補假)", "substitute"),
        ("（僅曼谷）", "bangkok_only"),
        ("(僅曼谷)", "bangkok_only"),
    )

    changed = True
    while changed:
        changed = False
        for suffix_text, suffix_code in suffix_patterns:
            if normalized.endswith(suffix_text):
                normalized = normalized[: -len(suffix_text)].strip()
                suffixes.insert(0, suffix_code)
                changed = True
                break

    names = dict(
        _HOLIDAY_TRANSLATIONS.get(
            normalized,
            {"zh-TW": normalized, "en": normalized, "th": normalized},
        )
    )
    for suffix_code in suffixes:
        localized_suffix = _LOCALIZED_SUFFIXES[suffix_code]
        for language in ("zh-TW", "en", "th"):
            names[language] = f"{names[language]}{localized_suffix[language]}"
    return names


def source_url_for_year(year: int, now: datetime | None = None) -> str:
    override = os.getenv("HOLIDAY_SOURCE_URL_TEMPLATE", "").strip()
    if override:
        return override.format(year=year)

    bangkok_now = now or datetime.now(ZoneInfo("Asia/Bangkok"))
    if year == bangkok_now.year:
        return CURRENT_YEAR_URL
    return ARCHIVE_URL_TEMPLATE.format(year=year)


def fetch_holiday_html(year: int) -> tuple[str, str]:
    url = source_url_for_year(year)
    timeout = float(os.getenv("HOLIDAY_SOURCE_TIMEOUT_SECONDS", "20"))
    user_agent = os.getenv(
        "HOLIDAY_SOURCE_USER_AGENT",
        "EmeraldLeaveSystem/14.4 (+holiday calendar synchronization)",
    )
    try:
        with httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": user_agent, "Accept-Language": "zh-TW,zh;q=0.9"},
        ) as client:
            response = client.get(url)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HolidaySourceError(f"Unable to download holiday source: {exc}") from exc

    if not response.text.strip():
        raise HolidaySourceError("Holiday source returned an empty page")
    return response.text, str(response.url)


def _extract_section_tokens(html: str, year: int) -> list[str]:
    parser = _TextTokenParser()
    parser.feed(html)
    parser.close()

    joined = "\n".join(parser.tokens)
    marker = re.compile(rf"泰國\s*節假日\s*{year}(?!\d)")
    matches = list(marker.finditer(joined))
    if not matches:
        raise HolidaySourceError(
            f"The page does not contain a Thailand holiday section for {year}; "
            "the publisher may not have released that year yet."
        )

    # The page contains navigation/calendar headings before the detailed list.
    # The last matching marker is the detailed holiday section.
    start = matches[-1].end()
    tail = joined[start:]
    end_match = re.search(r"節假日官方來源|備註", tail)
    if end_match:
        tail = tail[: end_match.start()]
    return [line.strip() for line in tail.splitlines() if line.strip()]


def _extract_name(fragments: list[str]) -> str:
    for fragment in fragments:
        text = re.sub(r"\s+", " ", fragment).strip(" ：:、")
        if not text:
            continue
        if text.startswith(_DESCRIPTION_PREFIXES):
            continue
        # When date/name/description are in one text node, keep only the first
        # whitespace-separated label and avoid importing the copyrighted prose.
        candidate = text.split(" ", 1)[0].strip()
        for prefix in _DESCRIPTION_PREFIXES:
            pos = candidate.find(prefix)
            if pos > 0:
                candidate = candidate[:pos]
        candidate = candidate.rstrip("。；;，,")
        if candidate:
            return candidate[:160]
    return ""


def _expand_entry(year: int, entry: _RawEntry, name: str) -> list[HolidayCandidate]:
    try:
        start = date(year, entry.month, entry.day)
        end = date(
            year,
            entry.end_month or entry.month,
            entry.end_day or entry.day,
        )
    except ValueError as exc:
        raise HolidaySourceError(f"Invalid date in holiday source: {exc}") from exc

    if end < start or (end - start).days > 14:
        raise HolidaySourceError(f"Invalid holiday date range: {start} to {end}")

    display_name = normalize_holiday_name(name, start)
    if entry.is_substitute and "補假" not in display_name:
        display_name = f"{display_name}（補假）"

    items: list[HolidayCandidate] = []
    cursor = start
    while cursor <= end:
        items.append(HolidayCandidate(date=cursor, name=display_name))
        cursor += timedelta(days=1)
    return items


def parse_holiday_html(html: str, year: int) -> list[HolidayCandidate]:
    """Parse only holiday dates and labels from the detailed Thailand section."""

    tokens = _extract_section_tokens(html, year)
    raw_entries: list[_RawEntry] = []
    current: _RawEntry | None = None
    current_month: int | None = None

    for token in tokens:
        match = _DATE_RE.match(token)
        if match:
            if current is not None:
                raw_entries.append(current)

            month_text = match.group("month")
            if month_text:
                current_month = int(month_text)
            if current_month is None:
                # A day-only token without prior month is not safely importable.
                current = None
                continue

            end_month_text = match.group("end_month")
            rest = match.group("rest").strip()
            current = _RawEntry(
                month=current_month,
                day=int(match.group("day")),
                end_month=int(end_month_text) if end_month_text else None,
                end_day=int(match.group("end_day")) if match.group("end_day") else None,
                is_substitute=bool(match.group("substitute")),
                fragments=[rest] if rest else [],
            )
            continue

        if current is not None:
            current.fragments.append(token)

    if current is not None:
        raw_entries.append(current)

    names = [_extract_name(entry.fragments) for entry in raw_entries]

    # Some source entries put the actual holiday on one line and the substitute
    # date plus label on the next line (for example "12月5日" / "7日補假 ...").
    # Backfill the unnamed actual date from the following substitute date.
    for index, name in enumerate(names):
        if name or index + 1 >= len(names):
            continue
        next_name = names[index + 1]
        if raw_entries[index + 1].is_substitute and next_name:
            names[index] = next_name.replace("（補假）", "")

    candidates: list[HolidayCandidate] = []
    for entry, name in zip(raw_entries, names, strict=True):
        if not name:
            continue
        candidates.extend(_expand_entry(year, entry, name))

    deduped: dict[tuple[date, str], HolidayCandidate] = {
        (item.date, item.name): item for item in candidates
    }
    result = sorted(deduped.values(), key=lambda item: (item.date, item.name))

    if len(result) < 5:
        raise HolidaySourceError(
            f"Only {len(result)} holidays were parsed for {year}; refusing a suspicious update."
        )
    return result
