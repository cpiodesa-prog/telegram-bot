# -*- coding: utf-8 -*-
"""Нові кадрові розпорядження мера: призначення, звільнення, покладення
виконання обов'язків (т.в.о.) та переведення.

Джерело: https://omr.gov.ua/ua/acts/mayor/ (та сама перша сторінка, що й
sessions.py). Кадрові розпорядження мають окрему нумерацію з суфіксом "К"
(наприклад №862К) — це надійніше, ніж самі лише ключові слова: слово
"призначення" трапляється і в розпорядженнях про стипендії, виплати,
склад комісій (номери БЕЗ "К") — нас цікавлять саме кадрові.

Перевірено на реальних даних mayor.json (442 записи, 2026 рік): keyword +
К-суфікс покривають усі 45 кадрових розпоряджень без винятку (0 пропусків).
"""
import sys, re, json
sys.stdout.reconfigure(encoding="utf-8")
import fetch
import scrape

PATH = "/ua/acts/mayor/"
KEYWORD_RE = re.compile(r"призначенн|звільненн|покладенн.*обов.?язк|переведенн", re.I)
K_SUFFIX_RE = re.compile(r"[КK]$")  # кирилична К або латинська K на кінці номера


def fetch_latest():
    """Свіжий (без кешу) фетч першої сторінки — вміст змінюється щодня."""
    html_text = fetch.get(scrape.BASE + PATH)
    return scrape.parse_rows(html_text)


def latest_personnel_changes():
    """Кадрові розпорядження (призначення/звільнення) серед найновіших записів."""
    rows = fetch_latest()
    return [r for r in rows if K_SUFFIX_RE.search(r["number"]) and KEYWORD_RE.search(r["description"])]


if __name__ == "__main__":
    events = latest_personnel_changes()
    print(f"Знайдено {len(events)} кадрових розпоряджень на першій сторінці:")
    print(json.dumps(events, ensure_ascii=False, indent=2))
