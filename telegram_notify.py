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


def send(text, token=None, chat_id=None, disable_preview=False, max_retries=5):
    token = token or os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = chat_id or os.environ["TELEGRAM_CHAT_ID"]
    for attempt in range(max_retries):
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
        if resp.ok:
            return resp.json()
        if resp.status_code == 429:
            # Telegram flood control — почекати стільки, скільки він просить, і повторити
            try:
                retry_after = resp.json().get("parameters", {}).get("retry_after", 5)
            except Exception:
                retry_after = 5
            print(f"  Telegram 429 (забагато запитів), чекаю {retry_after + 1}с і повторюю...")
            time.sleep(retry_after + 1)
            continue
        raise RuntimeError(f"Telegram API error {resp.status_code}: {resp.text}")
    raise RuntimeError(f"Telegram API: {max_retries} спроб і досі 429, здаюсь")


def send_many(messages, delay=1.5, **kw):
    """Надсилає список повідомлень з паузою (щоб не впертись у ліміти Telegram на канал)."""
    for i, text in enumerate(messages):
        send(text, **kw)
        if i < len(messages) - 1:
            time.sleep(delay)


if __name__ == "__main__":
    import sys
    send(sys.argv[1] if len(sys.argv) > 1 else "Тестове повідомлення від oms-notifier ✅")
    print("Надіслано.")
