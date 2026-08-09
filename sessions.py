# -*- coding: utf-8 -*-
"""Нові розпорядження міського голови про скликання сесій Одеської міської ради.

Джерело: https://omr.gov.ua/ua/acts/mayor/  (перша сторінка = найновіші записи,
достатньо для щоденної перевірки — нових розпоряджень мера рідко буває більше
кількох десятків за добу).

Розпорядження "Про скликання та порядок денний N сесії..." містить повний
текст порядку денного прямо на сторінці розпорядження (перевірено на прикладі
cache/proj_221690.html — та сама шаблонна сторінка acts/*), окремого файлу
шукати не треба — просто даємо посилання на саме розпорядження.
"""
import sys, re, json
sys.stdout.reconfigure(encoding="utf-8")
import fetch
import scrape

PATH = "/ua/acts/mayor/"
KEYWORD_RE = re.compile(r"скликанн", re.I)


def fetch_latest():
    """Свіжий (без кешу) фетч першої сторінки — вміст змінюється щодня."""
    html_text = fetch.get(scrape.BASE + PATH)
    return scrape.parse_rows(html_text)


def latest_sessions():
    """Розпорядження про скликання сесій серед найновіших записів."""
    rows = fetch_latest()
    return [r for r in rows if KEYWORD_RE.search(r["description"])]


if __name__ == "__main__":
    events = latest_sessions()
    print(f"Знайдено {len(events)} розпоряджень про скликання сесій на першій сторінці:")
    print(json.dumps(events, ensure_ascii=False, indent=2))
