# -*- coding: utf-8 -*-
"""Нові розпорядження про службові відрядження міського голови.

Джерело: https://omr.gov.ua/ua/acts/mayor/ (та сама перша сторінка, що й
sessions.py/personnel.py). Такі розпорядження мають окрему нумерацію з
суфіксом "Вд" (наприклад №12Вд) і в тексті завжди вказують напрямок,
строк відрядження та на кого покладається виконання обов'язків мера на
цей час — усе це вже є в тексті самого розпорядження за посиланням.

Перевірено на реальних даних mayor.json (442 записи, 2026 рік): лише 1
таке розпорядження за весь наявний період (№12Вд, 02.03.2026) — подія
рідкісна, тому фільтр лише за ключовим словом "відрядженн", без прив'язки
до суфікса "Вд" (замалий приклад, щоб довіряти суфіксу так само, як "К"
для кадрових — але жодних хибних збігів "відрядженн" в інших контекстах
серед 442 записів не знайдено, тож саме ключове слово вже надійне).
"""
import sys, re, json
sys.stdout.reconfigure(encoding="utf-8")
import fetch
import scrape

PATH = "/ua/acts/mayor/"
KEYWORD_RE = re.compile(r"відрядженн", re.I)


def fetch_latest():
    """Свіжий (без кешу) фетч першої сторінки — вміст змінюється щодня."""
    html_text = fetch.get(scrape.BASE + PATH)
    return scrape.parse_rows(html_text)


def latest_trips():
    rows = fetch_latest()
    return [r for r in rows if KEYWORD_RE.search(r["description"])]


if __name__ == "__main__":
    events = latest_trips()
    print(f"Знайдено {len(events)} розпоряджень про відрядження на першій сторінці:")
    print(json.dumps(events, ensure_ascii=False, indent=2))
