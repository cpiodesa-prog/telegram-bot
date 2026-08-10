# -*- coding: utf-8 -*-
"""Нові рішення виконкому Миколаївської міської ради.
Джерело: https://mkrada.gov.ua/documents/?c=5 (найновіші першими)."""
import sys, json
sys.stdout.reconfigure(encoding="utf-8")
import mk_scrape


def latest_vykonkom():
    return mk_scrape.fetch_latest(mk_scrape.CATEGORY_VYKONKOM)


if __name__ == "__main__":
    events = latest_vykonkom()
    print(f"Знайдено {len(events)} рішень виконкому на першій сторінці:")
    print(json.dumps(events, ensure_ascii=False, indent=2))
