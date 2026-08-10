# -*- coding: utf-8 -*-
"""Анонси засідань виконкому Миколаївської міської ради (подія, не рішення).

Джерело події: розділ "Анонси подій та заходів" (mk_calendar.py), відфільтрований
за ключовим словом "виконавч... коміте..." — аналог vykonkom_announce.py для
Одеси (там /ua/announce/). Конкретний порядок денний засідання підтягується
окремо зі сторінки-архіву (mk_agendas.py) і зіставляється за датою; якщо на
момент перевірки порядок денний ще не опубліковано — підставляється посилання
на загальний список порядків денних (він оновлюється сайтом сам).
"""
import sys, json, re
sys.stdout.reconfigure(encoding="utf-8")

import mk_calendar
import mk_agendas

KEYWORD_RE = re.compile(r"виконав\w*\s+коміт|засіданн\w*\s+виконком", re.I)


def latest_vykonkom_announcements():
    events = mk_calendar.fetch_announcements()
    agendas = None  # ліниво тягнемо лише якщо є хоч один релевантний анонс
    out = []
    for e in events:
        if not KEYWORD_RE.search(e["text"]):
            continue

        stream_url = None
        generic_agenda_link = None
        for link in e["links"]:
            if "youtube.com" in link:
                stream_url = link
            elif "poryadki-denni-zasidan-vikonkomu" in link:
                generic_agenda_link = link

        agenda_url = None
        if e["date_str"]:
            if agendas is None:
                agendas = mk_agendas.fetch_vykonkom_agendas()
            agenda_url = agendas.get(e["date_str"])
        if not agenda_url:
            agenda_url = generic_agenda_link or mk_agendas.AGENDA_LIST_URL

        out.append({
            "date": e["date_str"] or "?",
            "time": e["time"] or "",
            "text": e["text"],
            "agenda_url": agenda_url,
            "stream_url": stream_url,
        })
    return out


if __name__ == "__main__":
    events = latest_vykonkom_announcements()
    print(f"Знайдено {len(events)} анонсів засідань виконкому:")
    print(json.dumps(events, ensure_ascii=False, indent=2))
