# -*- coding: utf-8 -*-
"""Засідання постійних комісій Миколаївської міської ради.

Джерело: "Графік засідань постійних комісій" —
https://mkrada.gov.ua/content/grafik-zasidan12.html — щомісячна таблиця:
назва комісії, дата, час, місце/формат, контактний телефон; у комірці з
назвою комісії вбудоване й посилання "Посилання на порядок денний".

Рядки без призначеної дати (прочерк "-") пропускаються — це "порожні"
слоти графіка, а не реальні заплановані засідання.
"""
import sys, json, re
sys.stdout.reconfigure(encoding="utf-8")

import requests
from bs4 import BeautifulSoup

BASE = "https://mkrada.gov.ua"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; oms-notifier/1.0)"}
SCHEDULE_URL = f"{BASE}/content/grafik-zasidan12.html"
DATE_RE = re.compile(r"(\d{2})\.(\d{2})\.(\d{4})")


def latest_commission_meetings():
    resp = requests.get(SCHEDULE_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table")
    if not table:
        return []

    out = []
    for tr in table.find_all("tr"):
        cells = tr.find_all(["td", "th"])
        if len(cells) < 3:
            continue

        name_cell = cells[0]
        full_text = name_cell.get_text("\n", strip=True)
        if not full_text or full_text.lower().startswith("назва"):
            continue  # заголовок таблиці

        name = full_text.split("Посилання")[0].strip().rstrip(":").strip()
        if not name:
            continue

        a = name_cell.find("a", href=True)
        agenda_url = None
        if a:
            href = a["href"]
            agenda_url = href if href.startswith("http") else BASE + href

        date_text = cells[1].get_text(strip=True)
        m = DATE_RE.search(date_text)
        if not m:
            continue  # засідання ще не призначено ("-")
        date_str = f"{m.group(1)}.{m.group(2)}.{m.group(3)}"

        time_text = cells[2].get_text(strip=True) if len(cells) > 2 else ""

        out.append({
            "commission": name,
            "date": date_str,
            "time": time_text,
            "agenda_url": agenda_url or SCHEDULE_URL,
        })
    return out


if __name__ == "__main__":
    events = latest_commission_meetings()
    print(f"Знайдено {len(events)} запланованих засідань комісій:")
    print(json.dumps(events, ensure_ascii=False, indent=2))
