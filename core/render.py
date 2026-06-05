"""Рендер структурированного отчёта (core.numerology.report.build_report) в текст.

Текст plain (без Markdown — трактовки могут содержать спецсимволы) и разбивается
на сообщения ≤ лимита Telegram (4096).
"""

from __future__ import annotations

from datetime import date

TELEGRAM_LIMIT = 4096

_PSYCHO_ORDER = [
    "Характер",
    "Энергия",
    "Интерес",
    "Здоровье",
    "Логика, интуиция",
    "Труд, власть",
    "Везение",
    "Чувство долга",
    "Ум, память",
    "Самооценка",
    "Отношение к труду",
    "Целеустремлённость",
    "Качество семьянина",
    "Стабильность",
    "Темперамент",
]


def _val(v) -> str:
    return "нет" if v == 0 else str(v)


def _fmt_dates(iso_dates: list[str]) -> list[str]:
    return [date.fromisoformat(d).strftime("%d.%m.%Y") for d in iso_dates]


def render_report(report: dict, full_name: str, birth_date: date | None) -> str:
    """Собрать человекочитаемый plain-text отчёт из структуры build_report."""
    c = report["calculations"]
    pm = report["psychomatrix"]
    days = report["days"]
    fc = report["forecast"]
    ms = report["moon_sun"]
    pn = ms["personal_numbers"]

    born = f", р. {birth_date.strftime('%d.%m.%Y')}" if birth_date else ""
    L: list[str] = [f"🔮 НУМЕРОЛОГИЧЕСКАЯ МАТРИЦА\n{full_name}{born}"]

    danger = c["danger_age"] if c["danger_age"] is not None else "нет"
    L.append(
        "\n📊 ИСХОДНЫЕ ДАННЫЕ И ВЫЧИСЛЕНИЯ\n"
        f"Полных лет: {c['full_years']} · Прожито дней: {c['lived_days']}\n"
        f"Жизнь: {c['life_task']} · Духовный уровень: {c['spiritual_level']}\n"
        f"Код человека: {c['human_code']} · Код жизни: {c['life_code']}\n"
        f"Счастливые числа: {c['lucky_numbers']} · Финансовый код: {c['finance_code']}\n"
        f"Доступ к деньгам: {c['money_access']} · Жизненные силы: {c['vitality']}\n"
        f"Опасный возраст: {danger}"
    )

    q = {row["label"]: row for row in pm["qualities"]}
    sc = {row["label"]: row for row in pm["scalars"]}
    L.append("\n🧮 ПСИХОМАТРИЦА")
    L.append(" · ".join(f"{lbl}: {_val(q[lbl]['value'])}" for lbl in _PSYCHO_ORDER))
    L.append(
        f"Число души: {sc['Число души']['value']} · "
        f"ЧЖП: {sc['Число жизненного пути (ЧЖП)']['value']} · "
        f"Уровень сознания: {sc['Уровень сознания']['value']}\n"
        f"Код поведения: {sc['Код поведения']['value']}"
    )
    for lbl in _PSYCHO_ORDER:
        text = q[lbl]["text"]
        if text:
            L.append(f"• {lbl} ({_val(q[lbl]['value'])}): {text}")

    L.append("\n📅 БЛАГОПРИЯТНЫЕ / КРИТИЧЕСКИЕ / ТРАВМООПАСНЫЕ ДНИ")
    L.append(
        f"Благоприятные: {', '.join(_fmt_dates(days['favorable']))}\n"
        f"Критические: {', '.join(_fmt_dates(days['critical'])) or '—'}\n"
        f"Травмоопасные: {', '.join(_fmt_dates(days['traumatic']))}"
    )

    L.append("\n📈 ПРОГНОЗ НА 5 ЛЕТ")
    for f in fc:
        cyc = (
            f"; 12-цикл: {f['rebirth_cycle_text']}"
            if f["fate"] == "+" and f["rebirth_cycle_text"]
            else ""
        )
        sign = "+" if f["year_value"] >= 0 else ""
        L.append(
            f"{f['year']} (возраст {f['age']}): {f['personal_year']} — {f['personal_year_text']}; "
            f"Луна {f['moon']} / Солнце {f['sun']}; "
            f"год {sign}{f['year_value']} — {f['year_value_text']}; судьбоносный: {f['fate']}{cyc}"
        )

    L.append("\n🌙 ЛУНА И СОЛНЦЕ ПО МЕСЯЦАМ")
    L.append("\n".join(f"{m['month_name']}: {m['text']}" for m in ms["monthly"]))

    L.append("\n🗓 ЛИЧНЫЕ ЧИСЛА (на дату отчёта)")
    L.append(
        f"Год: {pn['personal_year']} · Месяц: {pn['personal_month']} · День: {pn['personal_day']}"
    )
    if pn["combo_title"]:
        L.append(f"{pn['combo_title']}\n{pn['combo_text']}")
    if pn["personal_month_text"]:
        L.append(f"Месяц: {pn['personal_month_text']}")
    if pn["personal_day_text"]:
        L.append(f"День: {pn['personal_day_text']}")

    return "\n".join(L)


def split_message(text: str, limit: int = TELEGRAM_LIMIT) -> list[str]:
    """Разбить длинный текст на части ≤ limit, не разрывая строки по возможности."""
    if len(text) <= limit:
        return [text]
    chunks: list[str] = []
    current = ""
    for line in text.split("\n"):
        while len(line) > limit:
            if current:
                chunks.append(current)
                current = ""
            chunks.append(line[:limit])
            line = line[limit:]
        if len(current) + len(line) + 1 > limit:
            chunks.append(current)
            current = line
        else:
            current = f"{current}\n{line}" if current else line
    if current:
        chunks.append(current)
    return chunks
