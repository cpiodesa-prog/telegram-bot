# -*- coding: utf-8 -*-
"""Спільна логіка розділу "Анонси подій та заходів" (/calendar/) mkrada.gov.ua.

Структура сторінки та пагінація (start=, по 10) ідентичні /documents/ —
кожен анонс лежить у <div class="news_line_item">. Методологія узята з
mkrada_parser.py (fetch_calendar_announcements), тут додатково витягуємо
ще й дату/час події та всі посилання всередині анонсу (порядок денний,
трансляція тощо), а не лише текст.
"""
import re
import time as _time
from datetime import date, timedelta

import requests
from bs4 import BeautifulSoup

BASE = "https://mkrada.gov.ua"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; oms-notifier/1.0)"}

UA_MONTHS = {
    "січня": 1, "лютого": 2, "березня": 3, "квітня": 4, "травня": 5, "червня": 6,
    "липня": 7, "серпня": 8, "вересня": 9, "жовтня": 10, "листопада": 11, "грудня": 12,
}
DATE_RE = re.compile(r"(\d{1,2})\s+([А-Яа-яЇїІіЄєҐґ']+)\s+(\d{4})", re.I)
TIME_RE = re.compile(r"(\d{1,2}:\d{2})")


def fetch_announcements(days_back=3, days_fwd=21, delay=0.3):
    """Анонси за період [сьогодні - days_back, сьогодні + days_fwd].
    Невеликий відступ назад — щоб не пропустити щойно проведену подію,
    якщо бот не запускався кілька днів; кілька тижнів вперед — анонси
    засідань виконкому зазвичай публікують заздалегідь."""
    d_from = date.today() - timedelta(days=days_back)
    d_to = date.today() + timedelta(days=days_fwd)
    results = []
    start = 0
    while True:
        url = (
            f"{BASE}/calendar/?c=0"
            f"&fd={d_from.day}&fm={d_from.month}&fy={d_from.year}"
            f"&td={d_to.day}&tm={d_to.month}&ty={d_to.year}"
            f"&o=0&s=&start={start}"
        )
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.select("div.news_line_item")
        if not items:
            break
        for div in items:
            text = div.get_text("\n", strip=True)
            links = []
            for a in div.select("a[href]"):
                href = a.get("href")
                if not href:
                    continue
                links.append(href if href.startswith("http") else BASE + href)

            dm = DATE_RE.search(text)
            tm = TIME_RE.search(text)
            ev_date = None
            if dm:
                d, mon_raw, y = dm.groups()
                mon = UA_MONTHS.get(mon_raw.lower())
                if mon:
                    ev_date = date(int(y), mon, int(d))

            results.append({
                "text": text,
                "date": ev_date,
                "date_str": f"{ev_date.day:02d}.{ev_date.month:02d}.{ev_date.year}" if ev_date else None,
                "time": tm.group(1) if tm else None,
                "links": links,
            })
        start += 10
        _time.sleep(delay)
    return results


if __name__ == "__main__":
    import json
    events = fetch_announcements()
    print(f"Анонсів знайдено: {len(events)}")
    print(json.dumps(
        [{**e, "date": e["date"].isoformat() if e["date"] else None} for e in events],
        ensure_ascii=False, indent=2,
    ))
