"""Рендер структурированного отчёта (core.numerology.report.build_report) в текст.

Текст plain (без Markdown — трактовки могут содержать спецсимволы) и разбивается
на сообщения ≤ лимита Telegram (4096).
"""

from __future__ import annotations

from datetime import UTC, date, datetime

TELEGRAM_LIMIT = 4096

# Энергопотенциал (РАСЧЕТ J) → человекочитаемый статус.
_ENERGY_TREND_TEXT = {2: "на подъёме", 1: "на подъёме", 0: "стабильно", -1: "на спаде"}

# Скаляры психоматрицы: атом → подпись в pm["scalars"].
_SCALAR_LABELS = [
    ("life_path", "Число жизненного пути (ЧЖП)"),
    ("soul_number", "Число души"),
    ("consciousness", "Уровень сознания"),
    ("behavior_code", "Код поведения"),
]

# Подписи аспектов мультиблоков (порядок = порядок диапазонов в extract_texts.py;
# индекс 0 — общее описание, выводится без подписи). Лист «текст» строки 224/238.
_LIFE_PATH_ASPECTS = [
    "",
    "Предназначение",
    "Недостатки",
    "Профессии",
    "Цвет удачи",
    "Талисман",
    "Число удачи",
]
_SOUL_ASPECTS = [
    "",
    "Эмоциональные особенности",
    "Недостатки",
    "Гармоничные отношения",
    "Счастливые числа",
    "Враждебные числа/дни/месяцы",
    "Счастливые даты/дни/месяцы",
    "Счастливые камни",
    "Счастливые цвета",
    "Болезни",
    "Рекомендации",
]
_ASPECT_LABELS = {"life_path": _LIFE_PATH_ASPECTS, "soul_number": _SOUL_ASPECTS}


def labeled_aspects(text, labels: list[str]) -> list[tuple[str, str]]:
    """Список аспектов мультиблока → пары (подпись, текст). Пустые и «прочерк» (─)
    пропускаются. Если text не список (одиночная трактовка) — одна пара без подписи."""
    if not isinstance(text, list):
        body = _as_text(text).strip()
        return [("", body)] if body else []
    out: list[tuple[str, str]] = []
    for i, aspect in enumerate(text):
        body = _as_text(aspect).strip()
        if not body or body in {"─", "-", "—"}:
            continue
        out.append((labels[i] if i < len(labels) else "", body))
    return out


def _as_text(value) -> str:
    """Трактовка interpret() может быть строкой или списком абзацев — в текст."""
    if isinstance(value, list):
        return "\n".join(str(v) for v in value)
    return str(value) if value else ""


def _want(report: dict, atom: str) -> bool:
    """Показывать ли атом: тариф задаёт report["_fields"]; нет ключа → показать всё."""
    fields = report.get("_fields")
    return fields is None or atom in fields


def _age_lt_30(birth_date: date | None) -> bool:
    """Возраст < 30 (для условного блока «Число души»). Без даты — считаем да."""
    if birth_date is None:
        return True
    today = datetime.now(UTC).date()
    before_bd = (today.month, today.day) < (birth_date.month, birth_date.day)
    return today.year - birth_date.year - before_bd < 30


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
    """Собрать человекочитаемый plain-text отчёт из структуры build_report.

    Рендерит только присутствующие секции — состав зависит от тарифа
    (см. core.numerology.tariffs)."""
    born = f", р. {birth_date.strftime('%d.%m.%Y')}" if birth_date else ""
    L: list[str] = [f"🔮 НУМЕРОЛОГИЧЕСКАЯ МАТРИЦА\n{full_name}{born}"]

    legacy = report.get("_fields") is None

    if "calculations" in report:
        c = report["calculations"]
        lines: list[str] = []
        if legacy:
            lines.append(f"Полных лет: {c['full_years']} · Прожито дней: {c['lived_days']}")
            lines.append(f"Жизнь: {c['life_task']} · Духовный уровень: {c['spiritual_level']}")
        if _want(report, "life_code"):
            lines.append(f"Код жизни: {c['life_code']}")
        if _want(report, "lucky_numbers"):
            lines.append(f"Счастливые числа: {c['lucky_numbers']}")
        if _want(report, "finance_code"):
            lines.append(f"Финансовый код удачи: {c['finance_code']}")
        if legacy:
            lines.append(f"Доступ к деньгам: {c['money_access']}")
        if _want(report, "vitality"):
            lines.append(f"Жизненные силы: {c['vitality']}")
        if _want(report, "energy_trend"):
            trend = _ENERGY_TREND_TEXT.get(c["energy_trend"], "стабильно")
            lines.append(f"Энергетический потенциал: {trend}")
        if _want(report, "danger_age"):
            danger = c["danger_age"] if c["danger_age"] is not None else "нет"
            lines.append(f"Опасный возраст: {danger}")
        if lines:
            L.append("\n📊 КОДЫ И ПОКАЗАТЕЛИ")
            L.append("\n".join(lines))
        # Кодировка жизни: два кода со сменой по возрасту (лист 18, до/после 35 лет).
        if _want(report, "human_code"):
            L.append("\n🧬 КОДИРОВКА ЖИЗНИ")
            L.append(f"До 35 лет — код {c['human_code']}:")
            if c.get("human_code_text"):
                L.append(_as_text(c["human_code_text"]))
            L.append(f"После 35 лет — код {c['second_code']}:")
            if c.get("second_code_text"):
                L.append(_as_text(c["second_code_text"]))

    if "psychomatrix" in report:
        pm = report["psychomatrix"]
        q = {row["label"]: row for row in pm["qualities"]}
        sc = {row["label"]: row for row in pm["scalars"]}
        if _want(report, "psychomatrix"):
            L.append("\n🧮 ПСИХОМАТРИЦА")
            L.append(" · ".join(f"{lbl}: {_val(q[lbl]['value'])}" for lbl in _PSYCHO_ORDER))
            for lbl in _PSYCHO_ORDER:
                text = q[lbl]["text"]
                if text:
                    L.append(f"• {lbl} ({_val(q[lbl]['value'])}): {text}")
        for atom, label in _SCALAR_LABELS:
            if not _want(report, atom):
                continue
            if atom == "soul_number" and not (legacy or _age_lt_30(birth_date)):
                continue
            row = sc[label]
            L.append(f"\n🔹 {label}: {_val(row['value'])}")
            aspects = _ASPECT_LABELS.get(atom)
            if aspects:
                for cap, body in labeled_aspects(row["text"], aspects):
                    L.append(f"• {cap}: {body}" if cap else body)
            elif row["text"]:
                L.append(_as_text(row["text"]))

    if "name" in report:
        nm = report["name"]
        name_parts = [
            f"{label}: {nm[key]}"
            for key, label in (
                ("last_name", "Фамилия"),
                ("first_name", "Имя"),
                ("middle_name", "Отчество"),
                ("maiden_name", "Девичья"),
            )
            if nm[key]
        ]
        if name_parts:
            flag = "есть" if nm["has_karma"] else "нет"
            L.append("\n🔤 ЧИСЛО И КАРМА ИМЕНИ")
            L.append(" · ".join(name_parts) + f"\nКарма имени: {nm['karma']} — {flag}")

    if "karma_events" in report:
        events = [
            e for e in (report["karma_events"]["first"], report["karma_events"]["second"]) if e
        ]
        if events:
            L.append("\n⚖️ КАРМИЧЕСКИЕ СОБЫТИЯ")
            L.extend(f"• {e['text']}" for e in events)

    if "days" in report:
        days = report["days"]
        L.append("\n📅 БЛАГОПРИЯТНЫЕ / КРИТИЧЕСКИЕ / ТРАВМООПАСНЫЕ ДНИ")
        L.append(
            f"Благоприятные: {', '.join(_fmt_dates(days['favorable']))}\n"
            f"Критические: {', '.join(_fmt_dates(days['critical'])) or '—'}\n"
            f"Травмоопасные: {', '.join(_fmt_dates(days['traumatic']))}"
        )

    if "forecast" in report:
        fc = report["forecast"]
        title = "ПРОГНОЗ НА ГОД" if len(fc) == 1 else f"ПРОГНОЗ НА {len(fc)} ЛЕТ"
        L.append(f"\n📈 {title}")
        for f in fc:
            sign = "+" if f["year_value"] >= 0 else ""
            L.append(
                f"\n— {f['year']} (возраст {f['age']}) · личное число года "
                f"{f['personal_year']} — {f['personal_year_text']}"
            )
            L.append(f"Луна {f['moon']} / Солнце {f['sun']} / ИТОГ {sign}{f['year_value']}")
            total = f.get("total_text") or f["year_value_text"]
            if total:
                L.append(f"Итог года: {_as_text(total)}")
            if f["sun"] == 0 and f.get("sun_text"):
                L.append(f"⚠️ Нулевой период: {_as_text(f['sun_text'])}")
            if f.get("life_force_text"):
                L.append(
                    f"График кода жизни (код {f['life_force_digit']}): "
                    f"{_as_text(f['life_force_text'])}"
                )
            if f["fate"] == "+":
                L.append("Судьбоносный год.")

    if "moon_sun" in report:
        ms = report["moon_sun"]
        pn = ms["personal_numbers"]
        if _want(report, "moon_sun_monthly"):
            L.append("\n🌙 ЛУНА И СОЛНЦЕ ПО МЕСЯЦАМ")
            L.append("\n".join(f"{m['month_name']}: {m['text']}" for m in ms["monthly"]))
        if _want(report, "personal_year"):
            L.append(f"\n🗓 ПЕРСОНАЛЬНОЕ ЧИСЛО ГОДА: {pn['personal_year']}")
            if pn["personal_year_text"]:
                L.append(_as_text(pn["personal_year_text"]))
        if _want(report, "personal_numbers"):
            L.append("\n🗓 ЛИЧНЫЕ ЧИСЛА МЕСЯЦА И ДНЯ (на дату отчёта)")
            L.append(f"Месяц: {pn['personal_month']} · День: {pn['personal_day']}")
            if pn["combo_title"]:
                L.append(f"{pn['combo_title']}\n{pn['combo_text']}")
            if pn["personal_month_text"]:
                L.append(f"Месяц: {pn['personal_month_text']}")
            if pn["personal_day_text"]:
                L.append(f"День: {pn['personal_day_text']}")

    return "\n".join(L)


def render_daily(forecast: dict, full_name: str | None = None) -> str:
    """Человекочитаемый прогноз на день из структуры daily.daily_forecast."""
    d = date.fromisoformat(forecast["date"]).strftime("%d.%m.%Y")
    who = f"\n{full_name}" if full_name else ""
    L: list[str] = [f"📅 ПРОГНОЗ НА ДЕНЬ · {d}{who}"]
    L.append(f"\n🔢 Личное число дня (ЧПД): {forecast['personal_day']}")
    if forecast["personal_day_text"]:
        L.append(_as_text(forecast["personal_day_text"]))
    L.append(f"\n🌿 Биоритм дня: {forecast['biorhythm']}")
    L.append(
        f"\n🗓 Контекст: личный год {forecast['personal_year']} · "
        f"личный месяц {forecast['personal_month']}"
    )
    if forecast["combo_title"]:
        L.append(f"{forecast['combo_title']}")
        if forecast["combo_text"]:
            L.append(_as_text(forecast["combo_text"]))
    elif forecast["personal_month_text"]:
        L.append(_as_text(forecast["personal_month_text"]))
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
