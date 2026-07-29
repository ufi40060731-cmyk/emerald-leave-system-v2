from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.holiday_sync import HolidaySourceError, parse_holiday_html, source_url_for_year


SAMPLE_HTML = """
<html><body>
<h2>泰國 節假日 1月-6月</h2>
<div>calendar content</div>
<h2>泰國 節假日 2026</h2>
<p><span>1月1日</span><strong>公曆新年</strong><span>慶祝公曆新年。</span></p>
<p><span>4月13日–15日</span><strong>宋干節（潑水節）</strong><span>泰國的傳統新年。</span></p>
<p><span>5月31日</span></p>
<p><span>6月1日補假</span><strong>佛誕節</strong><span>佛教節日。</span></p>
<p><span>6月3日 皇后華誕節</span><span>紀念王后生日。</span></p>
<p><span>12月5日</span></p>
<p><span>7日補假</span><strong>拉瑪九世誕辰日（父親節）</strong></p>
<p><span>12月10日</span><strong>憲法紀念日</strong></p>
<p><span>12月31日</span><strong>元旦前夕</strong></p>
<h2>節假日官方來源</h2>
</body></html>
"""


def test_parse_holiday_html_expands_ranges_and_substitutes():
    items = parse_holiday_html(SAMPLE_HTML, 2026)
    by_date = {item.date.isoformat(): item.name for item in items}

    assert by_date["2026-01-01"] == "公曆新年"
    assert by_date["2026-04-13"] == "宋干節（潑水節）"
    assert by_date["2026-04-14"] == "宋干節（潑水節）"
    assert by_date["2026-04-15"] == "宋干節（潑水節）"
    assert by_date["2026-05-31"] == "佛誕節"
    assert by_date["2026-06-01"] == "佛誕節（補假）"
    assert by_date["2026-12-05"] == "拉瑪九世國王普密蓬·阿杜德誕辰紀念日（父親節）"
    assert by_date["2026-12-07"] == "拉瑪九世誕辰日（父親節）（補假）"


def test_parser_rejects_wrong_year_page():
    with pytest.raises(HolidaySourceError):
        parse_holiday_html(SAMPLE_HTML, 2027)


def test_source_url_uses_live_page_for_current_year():
    now = datetime(2026, 7, 17, tzinfo=ZoneInfo("Asia/Bangkok"))
    assert source_url_for_year(2026, now).endswith("/calendar_zh_tw/thailand_zh_tw.html")
    assert source_url_for_year(2027, now).startswith("https://holidays-calendar.net/2027/")


def test_database_sync_preserves_confirmed_and_manual_rows(monkeypatch):
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import Session

    from app import main
    from app.holiday_sync import HolidayCandidate

    engine = create_engine("sqlite:///:memory:")
    main.Base.metadata.create_all(engine)

    monkeypatch.setattr(main, "fetch_holiday_html", lambda year: ("<html></html>", "https://example.test"))
    monkeypatch.setattr(
        main,
        "parse_holiday_html",
        lambda html, year: [
            HolidayCandidate(date=datetime(2026, 1, 1).date(), name="公曆新年"),
            HolidayCandidate(date=datetime(2026, 4, 6).date(), name="恰克里王朝開國紀念日"),
        ],
    )

    with Session(engine) as db:
        db.add_all(
            [
                main.Holiday(
                    country="TH",
                    year=2026,
                    date=datetime(2026, 1, 1).date(),
                    name="Old New Year Name",
                    holiday_type="official",
                    company_confirmed=True,
                    source="seed",
                ),
                main.Holiday(
                    country="TH",
                    year=2026,
                    date=datetime(2026, 7, 28).date(),
                    name="Removed unconfirmed seed",
                    holiday_type="official",
                    company_confirmed=False,
                    source="seed",
                ),
                main.Holiday(
                    country="TH",
                    year=2026,
                    date=datetime(2026, 9, 1).date(),
                    name="Company Foundation Day",
                    holiday_type="company",
                    company_confirmed=True,
                    source="manual",
                ),
            ]
        )
        db.commit()

        result = main.sync_holiday_year(db, 2026)
        rows = list(db.scalars(select(main.Holiday).order_by(main.Holiday.date)))

    assert result["added"] == 1
    assert result["updated"] == 1
    assert result["deleted"] == 1
    assert [(row.date.isoformat(), row.name, row.company_confirmed, row.source) for row in rows] == [
        ("2026-01-01", "公曆新年", True, "holidays-calendar.net"),
        ("2026-04-06", "恰克里王朝開國紀念日", False, "holidays-calendar.net"),
        ("2026-09-01", "Company Foundation Day", True, "manual"),
    ]


def test_parser_normalizes_mixed_language_fixed_date_names():
    html = """
    <html><body>
    <h2>泰國 節假日 2026</h2>
    <p><span>1月1日</span><strong>New Year（New Year's Day）</strong></p>
    <p><span>4月6日</span><strong>恰克里王朝開國紀念日</strong></p>
    <p><span>5月1日</span><strong>勞動節</strong></p>
    <p><span>6月3日</span><strong>皇后華誕節</strong></p>
    <p><span>7月28日</span><strong>國王誕辰日</strong></p>
    <p><span>8月12日</span><strong>母親節</strong></p>
    <p><span>10月13日</span><strong>國王逝世紀念日</strong></p>
    <p><span>10月23日</span><strong>五世皇紀念日</strong></p>
    <p><span>12月5日</span><strong>博碧·阿杜德（Bhumibol Adulyadej）國王陛下紀念日</strong></p>
    <p><span>12月10日</span><strong>泰王國憲法日（Constitution Day）</strong></p>
    <p><span>12月31日</span><strong>元旦前夕</strong></p>
    <h2>節假日官方來源</h2>
    </body></html>
    """
    by_date = {item.date.isoformat(): item.name for item in parse_holiday_html(html, 2026)}

    assert by_date["2026-12-05"] == "拉瑪九世國王普密蓬·阿杜德誕辰紀念日（父親節）"
    assert by_date["2026-12-10"] == "泰國憲法紀念日"


def test_localized_holiday_names_include_chinese_english_and_thai():
    from datetime import date

    from app.holiday_sync import localized_holiday_names

    names = localized_holiday_names("佛誕節（補假）", date(2026, 6, 1))

    assert names == {
        "zh-TW": "佛誕節（補假）",
        "en": "Visakha Bucha Day (substitute holiday)",
        "th": "วันวิสาขบูชา (วันหยุดชดเชย)",
    }


def test_localized_holiday_names_preserve_bangkok_only_suffix():
    from datetime import date

    from app.holiday_sync import localized_holiday_names

    names = localized_holiday_names("特別假期（僅曼谷）", date(2026, 10, 16))

    assert names["zh-TW"] == "特別假期（僅曼谷）"
    assert names["en"] == "Special holiday (Bangkok only)"
    assert names["th"] == "วันหยุดพิเศษ (เฉพาะกรุงเทพฯ)"
