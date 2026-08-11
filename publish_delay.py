# -*- coding: utf-8 -*-
"""Логування затримки між датою документа і фактичною публікацією на сайті.

Не впливає на сповіщення в Telegram — суто побічна аналітика для журналістки:
скільки днів минає між тим, як розпорядження підписане, і тим, як воно
реально стає доступним на сайті. Будь-яка помилка тут тихо ігнорується,
щоб аналітика ніколи не могла зламати основний прогін бота.

Одеса (omr.gov.ua): унизу сторінки кожного документа є службовий напис
"Сторінка створена: РРРР.ММ.ДД ГГ:ХХ" — момент, коли документ фактично
з'явився в публічному реєстрі. Підтверджено емпірично 11.08.2026:
розпорядження №1157К від 28.07.2026 отримало таку мітку лише 2026.08.11 —
на 14 днів пізніше підписання.

Миколаїв (mkrada.gov.ua): на сторінці документа є явний напис
"ОПУБЛІКОВАНО ДД.ММ.РРРР" (регекс стійкий до одруківок сайту — той самий
підхід, що й у дослідницькому mkrada_parser.py), без точного часу.

Результати пишуться в state/publish_delays.csv (append-only) — файл
комітиться в репозиторій разом з state/seen.json, і його можна відкрити
як звичайну таблицю для подальшого аналізу.
"""
import os, csv, re
from datetime import date, datetime

import requests
import fetch as omr_fetch  # PoW-солвер для omr.gov.ua (та ж логіка, що й у sessions.py тощо)
from mk_calendar import UA_MONTHS

LOG_FILE = os.path.join("state", "publish_delays.csv")
FIELDS = ["logged_at", "source", "category", "number", "date_signed", "date_published", "delay_days", "url"]

OMR_CREATED_RE = re.compile(r"Сторінка створена:\s*(\d{4})\.(\d{2})\.(\d{2})\s+(\d{1,2}):(\d{2})")
MK_PUBLISHED_RE = re.compile(r"КОВАНО\s*(\d{2})\.(\d{2})\.(\d{4})")  # стійко до "ОПУБЛІКОВАНО"/"ОПКБЛІКОВАНО" тощо

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; oms-notifier/1.0)"}


def _ensure_file():
    os.makedirs("state", exist_ok=True)
    is_new = not os.path.exists(LOG_FILE)
    if is_new:
        with open(LOG_FILE, "w", encoding="utf-8", newline="") as f:
            csv.DictWriter(f, fieldnames=FIELDS).writeheader()


def _append(row):
    _ensure_file()
    with open(LOG_FILE, "a", encoding="utf-8", newline="") as f:
        csv.DictWriter(f, fieldnames=FIELDS).writerow(row)


def _parse_ddmmyyyy(s):
    """Одеський формат дати в списку: '28.07.2026' -> date(2026,7,28)."""
    try:
        d, m, y = s.strip().split(".")
        return date(int(y), int(m), int(d))
    except Exception:
        return None


def _parse_ua_date(s):
    """Миколаївський формат дати в списку: '10 Липня 2026' -> date(2026,7,10)."""
    try:
        d, mon_raw, y = s.strip().split()
        mon = UA_MONTHS.get(mon_raw.lower())
        if not mon:
            return None
        return date(int(y), mon, int(d))
    except Exception:
        return None


def log_odesa(category, number, date_signed_str, url):
    """omr.gov.ua — сторінка документа за PoW-захистом, тому через fetch.py."""
    try:
        html_text = omr_fetch.get(url)
        m = OMR_CREATED_RE.search(html_text)
        if not m:
            return
        y, mo, d, hh, mm = m.groups()
        published_dt = datetime(int(y), int(mo), int(d), int(hh), int(mm))
        signed = _parse_ddmmyyyy(date_signed_str)
        delay_days = (published_dt.date() - signed).days if signed else ""
        _append({
            "logged_at": datetime.now().isoformat(timespec="seconds"),
            "source": "omr",
            "category": category,
            "number": number,
            "date_signed": date_signed_str,
            "date_published": published_dt.isoformat(sep=" ", timespec="minutes"),
            "delay_days": delay_days,
            "url": url,
        })
    except Exception:
        pass


def log_mykolaiv(category, number, date_signed_str, url):
    """mkrada.gov.ua — без anti-bot, звичайний requests."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        text = resp.content.decode("utf-8", errors="replace")
        m = MK_PUBLISHED_RE.search(text)
        if not m:
            return
        d, mo, y = m.groups()
        published = date(int(y), int(mo), int(d))
        signed = _parse_ua_date(date_signed_str)
        delay_days = (published - signed).days if signed else ""
        _append({
            "logged_at": datetime.now().isoformat(timespec="seconds"),
            "source": "mkrada",
            "category": category,
            "number": number,
            "date_signed": date_signed_str,
            "date_published": published.isoformat(),
            "delay_days": delay_days,
            "url": url,
        })
    except Exception:
        pass
