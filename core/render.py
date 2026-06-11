"""Рендер структурированного отчёта (core.numerology.report.build_report) в текст.

Текст plain (без Markdown — трактовки могут содержать спецсимволы) и разбивается
на сообщения ≤ лимита Telegram (4096).
"""

from __future__ import annotations

from datetime import UTC, date, datetime

from core.i18n import t
from core.numerology.matrix import monthly_energy_year

TELEGRAM_LIMIT = 4096

# Энергопотенциал (РАСЧЕТ J) → ключ i18n человекочитаемого статуса.
_ENERGY_TREND_KEY = {2: "trend.up", 1: "trend.up", 0: "trend.stable", -1: "trend.down"}


def energy_trend_text(value: int) -> str:
    """Статус энергопотенциала (на подъёме/стабильно/на спаде) на текущей локали."""
    return t(_ENERGY_TREND_KEY.get(value, "trend.stable"))


def vitality_text(value: int) -> str:
    """Описание «Жизненных сил» (РАСЧЕТ AN15): порог 27 на Matr!C12 (зашито в формулу)."""
    return t("txt.vitality_high") if value >= 27 else t("txt.vitality_low")


def money_access_text(value: int) -> str:
    """Описание «Доступа к деньгам» (РАСЧЕТ AN14): порог 27 на Matr!C11 (зашито в формулу)."""
    return t("txt.money_open") if value >= 27 else t("txt.money_love")


def thousand_code_text(i3: int) -> str | None:
    """«Код тысячника» (РАСЧЕТ C19) по Matr!I3. None — не тысячник (I3 не из набора).

    Тексты зашиты в формулу C19 (не в листе «текст»); набор кодов-тысячников дословно."""
    if i3 in (37, 38):
        return t("txt.thousand_teacher")
    if i3 == 19:
        return t("txt.thousand_creativity")
    if i3 in (28, 29):
        return t("txt.thousand_history")
    if i3 == 39 or i3 >= 46:
        return t("txt.thousand_teacher_history")
    return None


def consciousness_meaning(spiritual_level: int, life_task: int) -> str:
    """Текст уровня сознания (РАСЧЕТ C21). Зашит в формулу: ступени по духовному
    уровню (BD7=AN9) и жизненной задаче (Жизнь=AN8). Мёртвая ветка книги
    `IF(AN8<AN8,…)` трактована как «иначе» → «наблюдатель» (каноническое намерение)."""
    if spiritual_level < 20:
        return t("txt.consciousness_lt20")
    if life_task < 30:
        return t("txt.consciousness_lt30")
    if life_task < 40:
        return t("txt.consciousness_lt40")
    if life_task < 50:
        return t("txt.consciousness_lt50")
    return t("txt.consciousness_observer")


# Скаляры психоматрицы: атом → подпись в pm["scalars"].
_SCALAR_LABELS = [
    ("life_path", "Число жизненного пути (ЧЖП)"),
    ("soul_number", "Число души"),
    ("consciousness", "Уровень сознания"),
    ("behavior_code", "Код поведения"),
]

# Подписи аспектов мультиблоков — i18n-ключи (индекс 0 = общее описание без
# подписи). Лист «текст» строки 224/238. Перевод подставляется через t() при рендере.
_ASPECT_KEYS = {
    "life_path": ["", *[f"aspect.life_path.{i}" for i in range(1, 7)]],
    "soul_number": ["", *[f"aspect.soul.{i}" for i in range(1, 11)]],
}


def aspect_captions(atom: str) -> list[str]:
    """Переведённые подписи аспектов мультиблока (life_path/soul_number) на текущей локали."""
    return [t(k) if k else "" for k in _ASPECT_KEYS.get(atom, [])]


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
    "Таланты",
    "Темперамент",
    "Духовно-материальный баланс",
]


def _val(v) -> str:
    return "нет" if v == 0 else str(v)


def _fmt_dates(iso_dates: list[str]) -> list[str]:
    return [date.fromisoformat(d).strftime("%d.%m.%Y") for d in iso_dates]


def render_report(report: dict, full_name: str, birth_date: date | None) -> str:
    """Собрать человекочитаемый plain-text отчёт из структуры build_report.

    Рендерит только присутствующие секции — состав зависит от тарифа
    (см. core.numerology.tariffs)."""
    born = f", {t('lbl.born')} {birth_date.strftime('%d.%m.%Y')}" if birth_date else ""
    L: list[str] = [f"🔮 {t('sec.report_title')}\n{full_name}{born}"]

    legacy = report.get("_fields") is None

    if "calculations" in report:
        c = report["calculations"]
        lines: list[str] = []
        if legacy:
            lines.append(
                f"{t('lbl.full_years')}: {c['full_years']} · "
                f"{t('lbl.lived_days')}: {c['lived_days']}"
            )
            lines.append(
                f"{t('lbl.life')}: {c['life_task']} · "
                f"{t('lbl.spiritual_level')}: {c['spiritual_level']}"
            )
        if _want(report, "life_code"):
            lines.append(f"{t('lbl.life_code')}: {c['life_code']}")
            graph = c.get("life_code_graph_text")
            if graph:
                digit = c.get("life_code_graph_digit")
                lines.append(f"{t('lbl.life_code_graph').format(digit=digit)}: {_as_text(graph)}")
        if _want(report, "lucky_numbers"):
            lines.append(f"{t('lbl.lucky_numbers')}: {c['lucky_numbers']}")
        if _want(report, "finance_code"):
            lines.append(f"{t('lbl.finance_code')}: {c['finance_code']}")
        if legacy:
            lines.append(
                f"{t('lbl.money_access')}: {c['money_access']} — "
                f"{money_access_text(c['money_access'])}"
            )
        if _want(report, "vitality"):
            lines.append(f"{t('lbl.vitality')}: {c['vitality']} — {vitality_text(c['vitality'])}")
        if _want(report, "energy_trend"):
            lines.append(f"{t('lbl.energy_potential')}: {energy_trend_text(c['energy_trend'])}")
        if _want(report, "danger_age"):
            danger = c["danger_age"] if c["danger_age"] is not None else t("lbl.danger_none")
            lines.append(f"{t('lbl.danger_age')}: {danger}")
        if lines:
            L.append(f"\n📊 {t('sec.codes')}")
            L.append("\n".join(lines))
        # «Код тысячника» (РАСЧЕТ C19) — только для кодов-тысячников.
        if tc := thousand_code_text(c.get("thousand_code", 0)):
            L.append(f"\n⭐ {tc}")
        # Текст уровня сознания (РАСЧЕТ C21) по духовному уровню + жизненной задаче.
        if "spiritual_level" in c and "life_task" in c:
            L.append(f"\n🧭 {t('sec.spiritual')}")
            L.append(consciousness_meaning(c["spiritual_level"], c["life_task"]))
        # Кодировка жизни: два кода со сменой по возрасту (лист 18, до/после 35 лет).
        if _want(report, "human_code"):
            L.append(f"\n🧬 {t('sec.life_coding')}")
            L.append(f"{t('lbl.before_35').format(code=c['human_code'])}:")
            if c.get("human_code_text"):
                L.append(_as_text(c["human_code_text"]))
            L.append(f"{t('lbl.after_35').format(code=c['second_code'])}:")
            if c.get("second_code_text"):
                L.append(_as_text(c["second_code_text"]))

    if "psychomatrix" in report:
        pm = report["psychomatrix"]
        q = {row["label"]: row for row in pm["qualities"]}
        sc = {row["label"]: row for row in pm["scalars"]}
        if _want(report, "psychomatrix"):
            L.append(f"\n🧮 {t('sec.psychomatrix')}")
            L.append(
                " · ".join(f"{t('pm.' + lbl)}: {_val(q[lbl]['value'])}" for lbl in _PSYCHO_ORDER)
            )
            for lbl in _PSYCHO_ORDER:
                text = q[lbl]["text"]
                if text:
                    L.append(f"• {t('pm.' + lbl)} ({_val(q[lbl]['value'])}): {text}")
        for atom, label in _SCALAR_LABELS:
            if not _want(report, atom):
                continue
            if atom == "soul_number" and not (legacy or _age_lt_30(birth_date)):
                continue
            row = sc[label]
            L.append(f"\n🔹 {t('lbl.' + atom)}: {_val(row['value'])}")
            captions = aspect_captions(atom)
            if captions:
                for cap, body in labeled_aspects(row["text"], captions):
                    L.append(f"• {cap}: {body}" if cap else body)
            elif row["text"]:
                L.append(_as_text(row["text"]))

    if "name" in report:
        nm = report["name"]
        name_parts = [
            f"{t(label_key)}: {nm[key]}"
            for key, label_key in (
                ("last_name", "lbl.last_name"),
                ("first_name", "lbl.first_name"),
                ("middle_name", "lbl.middle_name"),
                ("maiden_name", "lbl.maiden_name"),
            )
            if nm[key]
        ]
        if name_parts:
            flag = t("lbl.karma_yes") if nm["has_karma"] else t("lbl.karma_no")
            L.append(f"\n🔤 {t('sec.name_karma')}")
            L.append(" · ".join(name_parts) + f"\n{t('lbl.karma_name')}: {nm['karma']} — {flag}")

    if "karma_events" in report:
        events = [
            e for e in (report["karma_events"]["first"], report["karma_events"]["second"]) if e
        ]
        if events:
            L.append(f"\n⚖️ {t('sec.karma_events')}")
            L.extend(f"• {e['text']}" for e in events)

    if "days" in report:
        days = report["days"]
        L.append(f"\n📅 {t('sec.days')}")
        L.append(
            f"{t('lbl.favorable')}: {', '.join(_fmt_dates(days['favorable']))}\n"
            f"{t('lbl.critical')}: {', '.join(_fmt_dates(days['critical'])) or '—'}\n"
            f"{t('lbl.traumatic')}: {', '.join(_fmt_dates(days['traumatic']))}"
        )

    if "forecast" in report:
        fc = report["forecast"]
        title = (
            t("sec.forecast_year") if len(fc) == 1 else t("lbl.forecast_n_years").format(n=len(fc))
        )
        L.append(f"\n📈 {title}")
        for f in fc:
            sign = "+" if f["year_value"] >= 0 else ""
            L.append(
                f"\n— {f['year']} ({t('lbl.age')} {f['age']}) · {t('lbl.personal_year_of')} "
                f"{f['personal_year']} — {f['personal_year_text']}"
            )
            L.append(
                f"{t('lbl.moon')} {f['moon']} / {t('lbl.sun')} {f['sun']} / "
                f"{t('lbl.total')} {sign}{f['year_value']}"
            )
            if f.get("energy_potential") is not None:
                L.append(f"{t('lbl.energy_potential')}: {energy_trend_text(f['energy_potential'])}")
            total = f.get("total_text") or f["year_value_text"]
            if total:
                L.append(f"{t('lbl.year_total')}: {_as_text(total)}")
            if f["sun"] == 0 and f.get("sun_text"):
                L.append(f"⚠️ {t('lbl.zero_period')}: {_as_text(f['sun_text'])}")
            if f["fate"] == "+" and f.get("rebirth_cycle_text"):
                L.append(f"{t('lbl.rebirth_cycle')}: {_as_text(f['rebirth_cycle_text'])}")
            if f.get("life_force_text"):
                L.append(
                    f"{t('lbl.life_code_graph').format(digit=f['life_force_digit'])}: "
                    f"{_as_text(f['life_force_text'])}"
                )
            if f["fate"] == "+":
                L.append(t("lbl.fateful_year"))

    if "moon_sun" in report:
        ms = report["moon_sun"]
        pn = ms["personal_numbers"]
        if _want(report, "moon_sun_monthly"):
            years = ms.get("monthly_years") or [{"year": None, "monthly": ms["monthly"]}]
            # «Энергетический график на текущий год» (Matr!CC28:CO28) — текстом по месяцам.
            cur_year = years[0].get("year")
            if "calculations" in report and birth_date and cur_year:
                me = monthly_energy_year(
                    report["calculations"]["life_code"], birth_date.year, cur_year
                )
                L.append(f"\n⚡ {t('sec.monthly_energy')}")
                L.append(" · ".join(f"{t(f'month_short.{i + 1}')} {v}" for i, v in enumerate(me)))
            if len(years) > 1:
                L.append(f"\n🌙 {t('sec.moon_sun_years')}")
                for yb in years:
                    L.append(f"\n— {yb['year']}:")
                    L.append("\n".join(f"{_month(m)}: {m['text']}" for m in yb["monthly"]))
            else:
                L.append(f"\n🌙 {t('sec.moon_sun')}")
                L.append("\n".join(f"{_month(m)}: {m['text']}" for m in years[0]["monthly"]))
        if _want(report, "personal_year"):
            L.append(f"\n🗓 {t('sec.personal_year')}: {pn['personal_year']}")
            if pn["personal_year_text"]:
                L.append(_as_text(pn["personal_year_text"]))
        if _want(report, "personal_numbers"):
            L.append(f"\n🗓 {t('sec.personal_numbers')}")
            L.append(
                f"{t('lbl.month')}: {pn['personal_month']} · {t('lbl.day')}: {pn['personal_day']}"
            )
            if pn["combo_title"]:
                L.append(f"{pn['combo_title']}\n{pn['combo_text']}")
            if pn["personal_month_text"]:
                L.append(f"{t('lbl.month')}: {pn['personal_month_text']}")
            if pn["personal_day_text"]:
                L.append(f"{t('lbl.day')}: {pn['personal_day_text']}")

    return "\n".join(L)


def _month(m: dict) -> str:
    """Локализованное имя месяца помесячного блока (month=1..12)."""
    return t(f"month.{m['month']}") if m.get("month") else str(m.get("month_name", ""))


def render_daily(forecast: dict, full_name: str | None = None) -> str:
    """Человекочитаемый прогноз на день из структуры daily.daily_forecast."""
    d = date.fromisoformat(forecast["date"]).strftime("%d.%m.%Y")
    who = f"\n{full_name}" if full_name else ""
    L: list[str] = [f"📅 {t('daily.title')} · {d}{who}"]
    L.append(f"\n🔢 {t('daily.personal_day')}: {forecast['personal_day']}")
    if forecast["personal_day_text"]:
        L.append(_as_text(forecast["personal_day_text"]))
    L.append(f"\n🌿 {t('daily.biorhythm')}: {forecast['biorhythm']}")
    L.append(
        "\n🗓 "
        + t("daily.context").format(
            year=forecast["personal_year"], month=forecast["personal_month"]
        )
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
