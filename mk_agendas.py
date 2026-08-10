# -*- coding: utf-8 -*-
"""Порядки денні засідань виконкому Миколаївської міської ради.

Джерело: https://mkrada.gov.ua/content/poryadki-denni-zasidan-vikonkomu.html —
статична сторінка зі списком посилань виду "ПОРЯДОК ДЕННИЙ засідання
виконавчого комітету ДД.ММ.РРРР" -> .docx/.pdf файл. Дата в тексті
посилання — дата ЗАСІДАННЯ (не дата публікації), тому саме за нею
можна зіставити конкретний порядок денний з анонсом у календарі
(mk_calendar.fetch_announcements) за той самий день.

Порядок денний зазвичай з'являється на сайті за день-два до засідання,
тому в день анонсу його може ще не бути — це нормально, viконком-модуль
підставляє посилання на загальний список як тимчасовий фолбек.
"""
import re
import requests
from bs4 import BeautifulSoup

BASE = "https://mkrada.gov.ua"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; oms-notifier/1.0)"}
AGENDA_LIST_URL = f"{BASE}/content/poryadki-denni-zasidan-vikonkomu.html"
DATE_RE = re.compile(r"(\d{2})\.(\d{2})\.(\d{4})")


def fetch_vykonkom_agendas():
    """Повертає {"дд.мм.рррр": url} для найновіших засідань (сторінка
    відсортована від найновіших зверху, тому в разі дублю дати перше
    знайдене посилання й лишається — set default, не перезаписуємо)."""
    resp = requests.get(AGENDA_LIST_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    out = {}
    for a in soup.select("a[href*='/files/']"):
        title = a.get_text(" ", strip=True)
        if "ПОРЯДОК ДЕННИЙ" not in title.upper():
            continue
        m = DATE_RE.search(title)
        if not m:
            continue
        key = f"{m.group(1)}.{m.group(2)}.{m.group(3)}"
        href = a.get("href")
        url = href if href.startswith("http") else BASE + href
        out.setdefault(key, url)
    return out


if __name__ == "__main__":
    agendas = fetch_vykonkom_agendas()
    print(f"Знайдено порядків денних: {len(agendas)}")
    for k, v in list(agendas.items())[:5]:
        print(k, "->", v)
