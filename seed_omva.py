# -*- coding: utf-8 -*-
"""Одноразовий сидинг стану для категорії "omva".

Навіщо: сторінка https://omr.gov.ua/ua/acts/omva/ показує ~50 записів на
першій сторінці (а не ~10, як у розпоряджень мера), тож перше ж реальне
ввімкнення категорії "omva" в run_daily.py розцінило б усі ~50 як "нові"
і спробувало б надіслати їх одним потоком у Telegram.

Цей скрипт запускається ОДИН РАЗ (вручну, через workflow_dispatch,
див. .github/workflows/daily-notify.yml) і позначає баченими всі
розпорядження ОМВА КРІМ N найновіших. Ці N лишаються "новими" й підуть
у Telegram при наступному звичайному запуску run_daily.py — як
компромісний "хвіст" останніх подій, а не всі 50 одразу.

Запуск:
    python seed_omva.py 10
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

import state
import omva


def seed(keep_n):
    st = state.load()
    events = omva.latest_omva_orders()  # найновіші першими
    to_mark = events[keep_n:]  # усе, крім keep_n найновіших

    for e in to_mark:
        state.mark_seen(st, "omva", e["url"])
    state.save(st)

    print(f"Знайдено {len(events)} розпоряджень ОМВА на першій сторінці.")
    print(f"Позначено баченими: {len(to_mark)} (усе, крім {keep_n} найновіших).")
    print(f"Лишились 'новими' (підуть у Telegram наступного разу, коли запуститься run_daily.py):")
    for e in events[:keep_n]:
        print(f"  №{e['number']} від {e['date']} — {e['description'][:70]}")


if __name__ == "__main__":
    keep_n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    seed(keep_n)
