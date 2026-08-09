# -*- coding: utf-8 -*-
"""Щоденний оркестратор: перевіряє нові скликання сесій, кадрові розпорядження
(призначення/звільнення), оголошення виконкому та засідання комісій Одеської
міськради, і шле нові у Telegram.

Запуск:
  python run_daily.py            # реальна відправка (потрібні TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID)
  python run_daily.py --dry-run  # тільки друкує в консоль, нічого не шле і не змінює state/seen.json

Використовується в .github/workflows/daily-notify.yml раз на день.
"""
import sys, os, re, argparse, html, traceback
sys.stdout.reconfigure(encoding="utf-8")

import state
import sessions
import personnel
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
    action = "Призначення" if re.search(r"призначенн", e["description"], re.I) else "Звільнення"
    icon = "🆕" if action == "Призначення" else "🔚"
    return (
        f"{icon} <b>Кадрове розпорядження: {action.lower()}</b>\n"
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


def run(dry_run=False):
    st = state.load()
    messages = []

    try:
        new_sessions = state.filter_new(st, "sessions", sessions.latest_sessions(), lambda e: e["url"])
        messages += [fmt_session(e) for e in new_sessions]
        print(f"[sessions] нових: {len(new_sessions)}")
    except Exception:
        print("[sessions] ПОМИЛКА:", file=sys.stderr)
        traceback.print_exc()

    try:
        new_pers = state.filter_new(st, "personnel", personnel.latest_personnel_changes(), lambda e: e["url"])
        messages += [fmt_personnel(e) for e in new_pers]
        print(f"[personnel] нових: {len(new_pers)}")
    except Exception:
        print("[personnel] ПОМИЛКА:", file=sys.stderr)
        traceback.print_exc()

    try:
        new_vk = state.filter_new(st, "vykonkom", vykonkom_announce.latest_vykonkom_announcements(), lambda e: e["url"])
        messages += [fmt_vykonkom(e) for e in new_vk]
        print(f"[vykonkom] нових: {len(new_vk)}")
    except Exception:
        print("[vykonkom] ПОМИЛКА:", file=sys.stderr)
        traceback.print_exc()

    try:
        new_comm = state.filter_new(st, "commissions", commissions.latest_commission_meetings(), commission_key)
        messages += [fmt_commission(e) for e in new_comm]
        print(f"[commissions] нових: {len(new_comm)}")
    except Exception:
        print("[commissions] ПОМИЛКА:", file=sys.stderr)
        traceback.print_exc()

    if not messages:
        print("Нових подій немає.")
        return

    if dry_run:
        print(f"\n[--dry-run] {len(messages)} повідомлень НЕ надіслано, state НЕ збережено:\n")
        for m in messages:
            print("----")
            print(m)
        return

    telegram_notify.send_many(messages)
    state.save(st)
    print(f"Надіслано {len(messages)} повідомлень, state оновлено.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    run(dry_run=args.dry_run)
