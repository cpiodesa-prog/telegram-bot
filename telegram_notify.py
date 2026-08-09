# -*- coding: utf-8 -*-
"""Надсилання повідомлень у Telegram-канал/групу через Bot API.

Потрібні змінні середовища:
  TELEGRAM_BOT_TOKEN — токен бота від @BotFather
  TELEGRAM_CHAT_ID   — id каналу/групи (напр. -1001234567890) або @username каналу

Дивись SETUP.md — там покроково, як їх отримати.
"""
import os, time
import requests

API = "https://api.telegram.org/bot{token}/sendMessage"


def send(text, token=None, chat_id=None, disable_preview=False):
    token = token or os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = chat_id or os.environ["TELEGRAM_CHAT_ID"]
    resp = requests.post(
        API.format(token=token),
        json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": disable_preview,
        },
        timeout=30,
    )
    if not resp.ok:
        raise RuntimeError(f"Telegram API error {resp.status_code}: {resp.text}")
    return resp.json()


def send_many(messages, delay=1.0, **kw):
    """Надсилає список повідомлень з невеликою паузою (щоб не впертись у ліміти Telegram)."""
    for i, text in enumerate(messages):
        send(text, **kw)
        if i < len(messages) - 1:
            time.sleep(delay)


if __name__ == "__main__":
    import sys
    send(sys.argv[1] if len(sys.argv) > 1 else "Тестове повідомлення від oms-notifier ✅")
    print("Надіслано.")
