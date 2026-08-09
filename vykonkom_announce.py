# -*- coding: utf-8 -*-
"""Нові оголошення про засідання Виконавчого комітету Одеської міської ради.

Джерело: https://omr.gov.ua/ua/announce/ — стрічка анонсів (картки, інша
розмітка ніж таблиці рішень/розпоряджень). Сторінка оголошення містить дату,
час, посилання на трансляцію та повний порядок денний засідання (перевірено
на cache/announce_vykonkom_2506.html).

Регулярка перевірена на cache/announce_p1.html: з 4 карток коректно
розпізнає всі, а за ключовим словом лишає саме анонс засідання виконкому.
"""
import sys, re, json
sys.stdout.reconfigure(encoding="utf-8")
import fetch
from scrape import BASE, clean

PATH = "/ua/announce/"

ROW_RE = re.compile(
    r'<div class="post[^"]*">.*?'
    r'<time class="date" datetime="(?P<date>[^"]*)">.*?'
    r'<strong class="title"><a href="(?P<link>[^"]+)"[^>]*>(?P<title>.*?)</a></strong>.*?'
    r'<div class="img-box">.*?</div>\s*'
    r'<p>(?P<desc>.*?)</p>',
    re.S)

KEYWORD_RE = re.compile(r"виконком|виконавч\w* коміте", re.I)


def parse_rows(htmltext):
    out = []
    for m in ROW_RE.finditer(htmltext):
        link = m.group("link")
        if link.startswith("/"):
            link = BASE + link
        out.append({
            "date": clean(m.group("date")),
            "title": clean(m.group("title")),
            "description": clean(m.group("desc")),
            "url": link,
        })
    return out


def fetch_latest():
    """Свіжий (без кешу) фетч стрічки анонсів — вміст змінюється щодня."""
    html_text = fetch.get(BASE + PATH)
    return parse_rows(html_text)


def latest_vykonkom_announcements():
    rows = fetch_latest()
    return [r for r in rows if KEYWORD_RE.search(r["title"]) or KEYWORD_RE.search(r["description"])]


if __name__ == "__main__":
    events = latest_vykonkom_announcements()
    print(f"Знайдено {len(events)} оголошень про засідання виконкому у стрічці:")
    print(json.dumps(events, ensure_ascii=False, indent=2))
