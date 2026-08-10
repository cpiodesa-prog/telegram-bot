# -*- coding: utf-8 -*-
"""Щоденний оркестратор: перевіряє нові скликання сесій, кадрові розпорядження
(призначення/звільнення), оголошення виконкому та засідання комісій Одеської
міськради, і шле нові у Telegram.

Запуск:
  python run_daily.py            # реальна відправка (потрібні TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID)
  python run_daily.py --dry-run  # тільки друкує в консоль, нічого не шле і не змінює state/seen.json

Використовується в .github/workflows/daily-notify.yml раз на день.
"""
import sys, os, re, time, argparse, html, traceback
sys.stdout.reconfigure(encoding="utf-8")

import state
import sessions
import personnel
import trips
import vykonkom_announce
import commissions
import telegram_notify


def esc(s):
    return html.escape(s or "", quote=False)


def fmt_session(e):
    return (
        f"🗓 <b>Скликання сесії Одеської міськради</b>\n"
        f"№{esc(e['number'])} від {esc(e['date'])}\n"
        f"{esc(e['description'])}\n"
        f"{e['url']}"
    )


def fmt_personnel(e):
    d = e["description"]
    if re.search(r"призначенн", d, re.I):
        action, icon = "Призначення", "🆕"
    elif re.search(r"звільненн", d, re.I):
        action, icon = "Звільнення", "🔚"
    elif re.search(r"покладенн.*обов.?язк", d, re.I):
        action, icon = "Покладення обов'язків (т.в.о.)", "⏳"
    elif re.search(r"переведенн", d, re.I):
        action, icon = "Переведення", "🔄"
    else:
        action, icon = "Кадрові зміни", "🧑‍💼"
    return (
        f"{icon} <b>Кадрове розпорядження: {action.lower()}</b>\n"
        f"№{esc(e['number'])} від {esc(e['date'])}\n"
        f"{esc(e['description'])}\n"
        f"{e['url']}"
    )


def fmt_trip(e):
    return (
        f"✈️ <b>Службове відрядження мера</b>\n"
        f"№{esc(e['number'])} від {esc(e['date'])}\n"
        f"{esc(e['description'])}\n"
        f"{e['url']}"
    )


def fmt_vykonkom(e):
    return (
        f"📋 <b>Засідання виконкому</b>\n"
        f"{esc(e['title'])}\n"
        f"{esc(e['description'])}\n"
        f"{e['url']}"
    )


def fmt_commission(e):
    lines = [
        f"🧩 <b>Засідання комісії</b>",
        f"{esc(e['commission'])}",
        f"{esc(e['date'])} {esc(e['time'])}" + (f", {esc(e['location'])}" if e.get("location") else ""),
    ]
    if e.get("commission_url"):
        lines.append(f"Комісія: {e['commission_url']}")
    if e.get("agenda_url"):
        lines.append(f"Порядок денний: {e['agenda_url']}")
    if e.get("stream_url"):
        lines.append(f"Трансляція: {e['stream_url']}")
    return "\n".join(lines)


def commission_key(e):
    return f"{e.get('commission_url')}|{e['date']}|{e['time']}"


CATEGORY_SOURCES = [
    ("sessions", sessions.latest_sessions, lambda e: e["url"], fmt_session),
    ("personnel", personnel.latest_personnel_changes, lambda e: e["url"], fmt_personnel),
    ("trips", trips.latest_trips, lambda e: e["url"], fmt_trip),
    ("vykonkom", vykonkom_announce.latest_vykonkom_announcements, lambda e: e["url"], fmt_vykonkom),
    ("commissions", commissions.latest_commission_meetings, commission_key, fmt_commission),
]


def process_category(st, name, fetch_fn, key_fn, fmt_fn, dry_run):
    """Фетчить категорію, шле нові повідомлення і одразу зберігає state —
    незалежно від категорії, збій в одній не чіпає прогрес інших."""
    try:
        events = fetch_fn()
    except Exception:
        print(f"[{name}] ПОМИЛКА фетчу:", file=sys.stderr)
        traceback.print_exc()
        return 0, 0

    new = state.get_new(st, name, events, key_fn)
    print(f"[{name}] нових: {len(new)}")
    if not new:
        return 0, 0

    if dry_run:
        for e in new:
            print("----")
            print(fmt_fn(e))
        return len(new), 0

    sent = 0
    try:
        for i, e in enumerate(new):
            telegram_notify.send(fmt_fn(e))
            state.mark_seen(st, name, key_fn(e))  # тільки ПІСЛЯ успішної відправки саме цієї події
            sent += 1
            if i < len(new) - 1:
                time.sleep(1.5)
    except Exception:
        print(f"[{name}] ПОМИЛКА відправки в Telegram (надіслано {sent}/{len(new)}):", file=sys.stderr)
        traceback.print_exc()
    finally:
        # зберігаємо стан навіть при частковому/невдалому надсиланні: те, що реально
        # пішло — зафіксовано, те, що ні — лишається "новим" і повториться наступного разу
        state.save(st)

    return len(new), sent


def run(dry_run=False):
    st = state.load()
    total_new = total_sent = 0

    for name, fetch_fn, key_fn, fmt_fn in CATEGORY_SOURCES:
        n, s = process_category(st, name, fetch_fn, key_fn, fmt_fn, dry_run)
        total_new += n
        total_sent += s

    if total_new == 0:
        print("Нових подій немає.")
    elif dry_run:
        print(f"\n[--dry-run] {total_new} нових подій, нічого не надіслано і не збережено.")
    else:
        print(f"Надіслано {total_sent}/{total_new} нових подій, state оновлено після кожної категорії.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    run(dry_run=args.dry_run)
