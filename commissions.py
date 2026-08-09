# -*- coding: utf-8 -*-
"""Нові засідання постійних депутатських комісій Одеської міської ради.

Джерело: https://deputat.omr.gov.ua/commissions/schedule/ — окремий
"депутатський портал", інший рушій ніж omr.gov.ua і БЕЗ anti-bot
(2waf/PoW) захисту, тому тут можна ходити звичайним requests, без fetch.py.

Таблиця графіка засідань поточного місяця має колонки:
Дата/час проведення | Комісія | Online трансляція | Порядок денний |
Протокол засідання | Дата розміщення

Перевірено вручну через mcp workspace web_fetch 2026-08-09 — структура
підтверджена (посилання на .docx/.pdf з порядком денним у 4-й колонці).
"""
import sys, re, json
sys.stdout.reconfigure(encoding="utf-8")
import requests
from bs4 import BeautifulSoup

URL = "https://deputat.omr.gov.ua/commissions/schedule/"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; oms-notifier/1.0)"}


def fetch_html():
    r = requests.get(URL, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text


def parse_schedule(html_text):
    soup = BeautifulSoup(html_text, "html.parser")
    table = soup.find("table")
    events = []
    if not table:
        return events
    for tr in table.find_all("tr"):
        cells = tr.find_all("td")
        if len(cells) < 6:
            continue
        dt_cell, comm_cell, stream_cell, agenda_cell, protocol_cell, posted_cell = cells[:6]

        dt_text = dt_cell.get_text(" ", strip=True)
        m = re.match(r"(\d{4}\.\d{2}\.\d{2})\s+(\d{2}:\d{2})", dt_text)
        date, time_ = (m.group(1), m.group(2)) if m else (dt_text, "")
        location = dt_text[m.end():].strip() if m else ""

        comm_link = comm_cell.find("a")
        commission = comm_link.get_text(strip=True) if comm_link else comm_cell.get_text(strip=True)
        commission_url = comm_link["href"] if comm_link and comm_link.has_attr("href") else None
        if commission_url and commission_url.startswith("/"):
            commission_url = "https://deputat.omr.gov.ua" + commission_url

        stream_link = stream_cell.find("a")
        stream_url = stream_link["href"] if stream_link and stream_link.has_attr("href") else None

        agenda_link = agenda_cell.find("a")
        agenda_url = agenda_link["href"] if agenda_link and agenda_link.has_attr("href") else None
        if agenda_url and agenda_url.startswith("/"):
            agenda_url = "https://deputat.omr.gov.ua" + agenda_url

        protocol_link = protocol_cell.find("a")
        protocol_url = protocol_link["href"] if protocol_link and protocol_link.has_attr("href") else None
        if protocol_url and protocol_url.startswith("/"):
            protocol_url = "https://deputat.omr.gov.ua" + protocol_url

        events.append({
            "date": date,
            "time": time_,
            "location": location,
            "commission": commission,
            "commission_url": commission_url,
            "stream_url": stream_url,
            "agenda_url": agenda_url,
            "protocol_url": protocol_url,
            "posted": posted_cell.get_text(strip=True),
        })
    return events


def latest_commission_meetings():
    """Графік засідань поточного місяця (сторінка за замовчуванням)."""
    return parse_schedule(fetch_html())


if __name__ == "__main__":
    events = latest_commission_meetings()
    print(f"Знайдено {len(events)} засідань комісій у поточному місяці:")
    print(json.dumps(events, ensure_ascii=False, indent=2))
