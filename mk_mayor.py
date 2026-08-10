# -*- coding: utf-8 -*-
"""Нові розпорядження міського голови Миколаєва.
Джерело: https://mkrada.gov.ua/documents/?c=4 (найновіші першими)."""
import sys, json
sys.stdout.reconfigure(encoding="utf-8")
import mk_scrape


def latest_mayor_orders():
    return mk_scrape.fetch_latest(mk_scrape.CATEGORY_MAYOR)


if __name__ == "__main__":
    events = latest_mayor_orders()
    print(f"Знайдено {len(events)} розпоряджень мера на першій сторінці:")
    print(json.dumps(events, ensure_ascii=False, indent=2))
