# -*- coding: utf-8 -*-
"""Просте сховище "вже бачених" подій, щоб не слати одне й те саме двічі.

Стан зберігається у state/seen.json — файл комітиться назад у репозиторій
після кожного запуску GitHub Actions (див. .github/workflows/daily-notify.yml),
тому історія переживає між запусками без бази даних.
"""
import os, json

STATE_DIR = "state"
STATE_FILE = os.path.join(STATE_DIR, "seen.json")

CATEGORIES = ["sessions", "vykonkom", "commissions", "personnel"]


def load():
    if not os.path.exists(STATE_FILE):
        return {c: [] for c in CATEGORIES}
    data = json.load(open(STATE_FILE, encoding="utf-8"))
    for c in CATEGORIES:
        data.setdefault(c, [])
    return data


def save(state):
    os.makedirs(STATE_DIR, exist_ok=True)
    # тримаємо лише останні 500 ключів на категорію, щоб файл не розростався
    trimmed = {c: state.get(c, [])[-500:] for c in CATEGORIES}
    json.dump(trimmed, open(STATE_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def filter_new(state, category, events, key_fn):
    """Повертає лише ті events, чийого ключа ще нема у state[category],
    і одразу дописує нові ключі у state (in-place)."""
    seen = set(state.get(category, []))
    fresh = [e for e in events if key_fn(e) not in seen]
    for e in fresh:
        state.setdefault(category, []).append(key_fn(e))
    return fresh
