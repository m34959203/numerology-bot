"""Генерация PDF-отчёта (reportlab) с поддержкой кириллицы.

Дизайн «редакторско-небесный»: тёплая бумага, индиговые чернила, латунный
акцент на числах. Шрифты PT Serif (заголовки/числа) + PT Sans (текст)
бандлятся в репо (core/assets/fonts/, лицензия SIL OFL). Если их нет — fallback
на системный DejaVuSans (apt-get install fonts-dejavu-core).

Экранируется ТОЛЬКО динамический текст (трактовки/имена) — структурные теги
reportlab (<b>, <br/>, <font>) остаются рабочими.
"""

from __future__ import annotations

from datetime import date
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.doctemplate import NextPageTemplate

from bot.config import settings
from core.charts import life_code_energy, life_force_curve, monthly_energy
from core.numerology.matrix import energy_curve, life_code_digits, monthly_energy_year
from core.render import (
    _ASPECT_LABELS,
    _ENERGY_TREND_TEXT,
    _SCALAR_LABELS,
    _age_lt_30,
    _as_text,
    _fmt_dates,
    _val,
    _want,
    labeled_aspects,
    money_access_text,
    vitality_text,
)

# --- палитра (RGB для печати; OKLCH-логика подобрана на глаз) ----------------
PAPER = colors.HexColor("#FBF8F3")  # тёплый off-white, не чистый белый
INK = colors.HexColor("#1E2340")  # глубокий индиго, не #000
ACCENT = colors.HexColor("#A8761F")  # латунь/охра — держит числа
MUTED = colors.HexColor("#6B6E84")  # приглушённый индиго-серый для подписей
RULE = colors.HexColor("#E2DACB")  # тёплая линейка-хейрлайн

# --- шрифты ------------------------------------------------------------------
_SERIF = "PTSerif"
_SERIF_B = "PTSerif-Bold"
_SANS = "PTSans"
_SANS_B = "PTSans-Bold"

_ASSETS = Path(__file__).resolve().parent / "assets" / "fonts"
# (имя reportlab, [пути-кандидаты]); первый существующий — побеждает
_FONT_SETS = {
    _SERIF: [_ASSETS / "PTSerif-Regular.ttf"],
    _SERIF_B: [_ASSETS / "PTSerif-Bold.ttf"],
    _SANS: [_ASSETS / "PTSans-Regular.ttf"],
    _SANS_B: [_ASSETS / "PTSans-Bold.ttf"],
}
_DEJAVU = {
    "regular": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
    ],
    "bold": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    ],
}

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
# Квадрат Пифагора: позиция в сетке → (индекс качества 0..8, короткая подпись).
# Раскладка столбцами 1-2-3 / 4-5-6 / 7-8-9 (канон).
_GRID = [
    [(0, "Характер"), (3, "Здоровье"), (6, "Везение")],
    [(1, "Энергия"), (4, "Логика"), (7, "Долг")],
    [(2, "Интерес"), (5, "Труд"), (8, "Память")],
]
_fonts_ready = False


def _first_existing(paths) -> str | None:
    for p in paths:
        if Path(p).exists():
            return str(p)
    return None


def _ensure_fonts() -> None:
    """Регистрирует PT Serif/Sans из репо; при отсутствии — DejaVu fallback."""
    global _fonts_ready
    if _fonts_ready:
        return
    dejavu_reg = _first_existing(_DEJAVU["regular"]) or _first_existing([settings.pdf_font_path])
    dejavu_bold = _first_existing(_DEJAVU["bold"]) or dejavu_reg
    fallback = {_SERIF: dejavu_reg, _SERIF_B: dejavu_bold, _SANS: dejavu_reg, _SANS_B: dejavu_bold}
    for name, candidates in _FONT_SETS.items():
        path = _first_existing(candidates) or fallback[name]
        if path is None:
            raise RuntimeError(
                "Не найден ни бандл PT-шрифтов (assets/fonts/), ни системный "
                "DejaVuSans. Установите fonts-dejavu-core или задайте PDF_FONT_PATH."
            )
        pdfmetrics.registerFont(TTFont(name, path))
    _fonts_ready = True


def fonts_available() -> bool:
    """True, если есть годный шрифт (бандл PT или системный DejaVu). Для тестов."""
    try:
        _ensure_fonts()
        return True
    except RuntimeError:
        return False


def _styles() -> dict[str, ParagraphStyle]:
    body = ParagraphStyle(
        "body", fontName=_SANS, fontSize=10, leading=15, textColor=INK, alignment=TA_LEFT
    )
    return {
        "body": body,
        "lead": ParagraphStyle("lead", parent=body, textColor=MUTED, fontSize=10.5, leading=15),
        # секционный заголовок: трекинг-капс акцентом (линейку рисуем отдельно)
        "section": ParagraphStyle(
            "section",
            parent=body,
            fontName=_SANS_B,
            fontSize=10.5,
            leading=13,
            textColor=ACCENT,
            spaceBefore=2,
            spaceAfter=2,
        ),
        "interp": ParagraphStyle("interp", parent=body, spaceBefore=3, leading=14.5),
        "kv_key": ParagraphStyle(
            "kv_key", parent=body, fontName=_SANS, fontSize=8.5, textColor=MUTED, leading=11
        ),
        "kv_val": ParagraphStyle(
            "kv_val", parent=body, fontName=_SERIF_B, fontSize=12, textColor=INK, leading=14
        ),
        # обложка
        "kicker": ParagraphStyle(
            "kicker",
            parent=body,
            fontName=_SANS_B,
            fontSize=11,
            textColor=ACCENT,
            alignment=TA_CENTER,
            leading=15,
        ),
        "cover_name": ParagraphStyle(
            "cover_name",
            parent=body,
            fontName=_SERIF_B,
            fontSize=30,
            leading=36,
            textColor=INK,
            alignment=TA_CENTER,
        ),
        "cover_meta": ParagraphStyle(
            "cover_meta",
            parent=body,
            fontSize=11,
            textColor=MUTED,
            alignment=TA_CENTER,
            leading=16,
        ),
        "hero_num": ParagraphStyle(
            "hero_num",
            parent=body,
            fontName=_SERIF_B,
            fontSize=58,
            leading=60,
            textColor=ACCENT,
            alignment=TA_CENTER,
        ),
        "hero_label": ParagraphStyle(
            "hero_label",
            parent=body,
            fontName=_SANS_B,
            fontSize=10,
            textColor=MUTED,
            alignment=TA_CENTER,
            leading=14,
        ),
        # ячейка психоматрицы
        "cell_num": ParagraphStyle(
            "cell_num",
            parent=body,
            fontName=_SERIF_B,
            fontSize=19,
            leading=22,
            textColor=ACCENT,
            alignment=TA_CENTER,
        ),
        "cell_empty": ParagraphStyle(
            "cell_empty",
            parent=body,
            fontName=_SERIF,
            fontSize=19,
            leading=22,
            textColor=RULE,
            alignment=TA_CENTER,
        ),
        "cell_label": ParagraphStyle(
            "cell_label",
            parent=body,
            fontName=_SANS,
            fontSize=7,
            leading=9,
            textColor=MUTED,
            alignment=TA_CENTER,
        ),
    }


def _e(value) -> str:
    """Экранировать динамический текст для разметки reportlab Paragraph."""
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _track(text: str) -> str:
    """Трекинг-капс: разрядка букв (у Paragraph нет letter-spacing).

    Неразрывные пробелы (U+00A0) reportlab не схлопывает (обычные — да, и
    граница слов пропадает). Внутри слова буквы через nbsp, между словами — три.
    """
    nbsp = "\u00a0"
    words = text.upper().split(" ")
    return (nbsp * 3).join(nbsp.join(_e(ch) for ch in w) for w in words)


# ширина рабочей области (A4 минус поля)
_L = _R = 18 * mm
_T = 16 * mm
_B = 18 * mm
_CW = A4[0] - _L - _R


def _section(flow: list, styles: dict, title: str) -> None:
    flow.append(Spacer(1, 14))
    flow.append(Paragraph(_track(title), styles["section"]))
    flow.append(
        Table(
            [[""]],
            colWidths=[_CW],
            style=TableStyle([("LINEABOVE", (0, 0), (-1, -1), 0.6, RULE)]),
        )
    )
    flow.append(Spacer(1, 6))


def _kv_table(styles: dict, pairs: list[tuple[str, str]], cols: int = 3) -> Table:
    """Сетка ключ→значение: подпись приглушённым сансом, значение серифом."""
    cells = []
    for key, val in pairs:
        block = [
            Paragraph(_e(key), styles["kv_key"]),
            Paragraph(_e(val), styles["kv_val"]),
        ]
        cells.append(block)
    rows = [cells[i : i + cols] for i in range(0, len(cells), cols)]
    while rows and len(rows[-1]) < cols:
        rows[-1].append([])
    col_w = _CW / cols
    return Table(
        rows,
        colWidths=[col_w] * cols,
        style=TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        ),
    )


def _psychomatrix_grid(styles: dict, q: dict) -> Table:
    """Квадрат Пифагора 3×3: повтор-число крупно + подпись качества."""
    data = []
    for grid_row in _GRID:
        out = []
        for idx, short in grid_row:
            label = _PSYCHO_ORDER[idx]
            value = q[label]["value"]
            num = str(value) if value else "—"
            st = styles["cell_num"] if value else styles["cell_empty"]
            out.append(
                [Paragraph(num, st), Spacer(1, 1), Paragraph(_track(short), styles["cell_label"])]
            )
        data.append(out)
    side = min(_CW / 3, 46 * mm)
    return Table(
        data,
        colWidths=[side] * 3,
        rowHeights=[side * 0.62] * 3,
        hAlign="CENTER",
        style=TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.6, RULE),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        ),
    )


def _hero_number(report: dict) -> tuple[str, str] | None:
    """Одно «геройское» число для обложки, адаптивно к составу тарифа."""
    pm = report.get("psychomatrix")
    if pm:
        sc = {row["label"]: row for row in pm["scalars"]}
        v = sc.get("Число жизненного пути (ЧЖП)")
        if v:
            return str(v["value"]), "Число жизненного пути"
    ms = report.get("moon_sun")
    if ms:
        return str(ms["personal_numbers"]["personal_year"]), "Личное число года"
    c = report.get("calculations")
    if c and c.get("life_task") is not None:
        return str(c["life_task"]), "Жизненная задача"
    return None


def _cover(flow: list, styles: dict, report: dict, full_name: str, birth_date: date | None) -> None:
    flow.append(Spacer(1, 70))
    flow.append(Paragraph(_track("Нумерологическая матрица"), styles["kicker"]))
    flow.append(Spacer(1, 10))
    flow.append(
        Table(
            [[""]],
            colWidths=[40 * mm],
            hAlign="CENTER",
            style=TableStyle([("LINEABOVE", (0, 0), (-1, -1), 0.8, ACCENT)]),
        )
    )
    flow.append(Spacer(1, 26))
    flow.append(Paragraph(_e(full_name), styles["cover_name"]))
    flow.append(Spacer(1, 8))
    meta = []
    if birth_date:
        meta.append(f"дата рождения {birth_date.strftime('%d.%m.%Y')}")
    flow.append(Paragraph(" · ".join(meta) if meta else "&nbsp;", styles["cover_meta"]))

    hero = _hero_number(report)
    if hero:
        flow.append(Spacer(1, 54))
        flow.append(Paragraph(hero[0], styles["hero_num"]))
        flow.append(Paragraph(_track(hero[1]), styles["hero_label"]))
    flow.append(PageBreak())


def build_report_pdf(report: dict, full_name: str, birth_date: date | None) -> bytes:
    """Собрать PDF-отчёт из структуры build_report. Возвращает bytes."""
    _ensure_fonts()
    s = _styles()
    flow: list = []

    _cover(flow, s, report, full_name, birth_date)

    # Рендерим только присутствующие секции — состав зависит от тарифа.
    legacy = report.get("_fields") is None

    if "calculations" in report:
        c = report["calculations"]
        pairs: list[tuple[str, str]] = []
        if legacy:
            pairs += [
                ("Полных лет", str(c["full_years"])),
                ("Прожито дней", str(c["lived_days"])),
                ("Жизненная задача", str(c["life_task"])),
                ("Духовный уровень", str(c["spiritual_level"])),
            ]
        if _want(report, "life_code"):
            pairs.append(("Код жизни", str(c["life_code"])))
        if _want(report, "lucky_numbers"):
            pairs.append(("Счастливые числа", str(c["lucky_numbers"])))
        if _want(report, "finance_code"):
            pairs.append(("Финансовый код удачи", str(c["finance_code"])))
        if legacy:
            ma = c["money_access"]
            pairs.append(("Доступ к деньгам", f"{ma} — {money_access_text(ma)}"))
        if _want(report, "vitality"):
            pairs.append(("Жизненные силы", f"{c['vitality']} — {vitality_text(c['vitality'])}"))
        if _want(report, "energy_trend"):
            pairs.append(
                ("Энергопотенциал", _ENERGY_TREND_TEXT.get(c["energy_trend"], "стабильно"))
            )
        if _want(report, "danger_age"):
            danger = c["danger_age"] if c["danger_age"] is not None else "нет"
            pairs.append(("Опасный возраст", str(danger)))
        if pairs:
            _section(flow, s, "Коды от даты рождения")
            flow.append(_kv_table(s, pairs))
        # «График кода жизни» под числом «Код жизни» — разворот ссылки-на-описание
        # из РАСЧЕТ (лист 19, текст!B212), паритет с текстом (фидбэк 11.06.2026).
        if _want(report, "life_code") and c.get("life_code_graph_text"):
            digit = c.get("life_code_graph_digit")
            flow.append(
                Paragraph(
                    f"<b>График кода жизни (код {digit}).</b> "
                    f"{_e(_as_text(c['life_code_graph_text']))}",
                    s["body"],
                )
            )
        # «График жизненной энергии» (лист 19, F21:K21) — столбцы 6 цифр кода жизни.
        if _want(report, "life_code"):
            _ensure_fonts()
            flow.append(Paragraph("<b>График жизненной энергии</b>", s["interp"]))
            flow.append(life_code_energy(life_code_digits(c["life_code"]), _SANS))
        # Кодировка жизни: два кода со сменой по возрасту (лист 18, до/после 35 лет).
        if _want(report, "human_code"):
            _section(flow, s, "Кодировка жизни")
            for cap, code_key, text_key in (
                ("До 35 лет", "human_code", "human_code_text"),
                ("После 35 лет", "second_code", "second_code_text"),
            ):
                flow.append(
                    Paragraph(
                        f"<font color='#A8761F'><b>{cap} · код {_e(c[code_key])}.</b></font>",
                        s["interp"],
                    )
                )
                if c.get(text_key):
                    flow.append(Paragraph(_e(_as_text(c[text_key])), s["body"]))

    if "psychomatrix" in report:
        pm = report["psychomatrix"]
        q = {row["label"]: row for row in pm["qualities"]}
        sc = {row["label"]: row for row in pm["scalars"]}
        if _want(report, "psychomatrix"):
            _section(flow, s, "Психоматрица · квадрат Пифагора")
            flow.append(_psychomatrix_grid(s, q))
            flow.append(Spacer(1, 8))
            # Производные качества (суммы рядов/столбцов/диагоналей) — числами, как в РАСЧЕТ.
            derived = " · ".join(f"{lbl} {_val(q[lbl]['value'])}" for lbl in _PSYCHO_ORDER[9:])
            flow.append(Paragraph(f"<font color='#6B6E84'>{_e(derived)}</font>", s["body"]))
            flow.append(Spacer(1, 6))
            for lbl in _PSYCHO_ORDER:
                text = q[lbl]["text"]
                if text:
                    val = _val(q[lbl]["value"])
                    flow.append(
                        Paragraph(
                            f"<b>{_e(lbl)}</b> <font color='#A8761F'>{val}</font> — {_e(text)}",
                            s["interp"],
                        )
                    )
        for atom, label in _SCALAR_LABELS:
            if not _want(report, atom):
                continue
            if atom == "soul_number" and not (legacy or _age_lt_30(birth_date)):
                continue
            row = sc[label]
            _section(flow, s, label)
            val = _val(row["value"])
            flow.append(
                Paragraph(
                    f"<font name='{_SERIF_B}' size='15' color='#A8761F'>{val}</font>",
                    s["interp"],
                )
            )
            aspects = _ASPECT_LABELS.get(atom)
            if aspects:
                for cap, body in labeled_aspects(row["text"], aspects):
                    prefix = f"<b>{_e(cap)}.</b> " if cap else ""
                    flow.append(Paragraph(prefix + _e(body), s["body"]))
            elif row["text"]:
                flow.append(Paragraph(_e(_as_text(row["text"])), s["body"]))

    if "name" in report:
        nm = report["name"]
        name_pairs = [
            (label, nm[key])
            for key, label in (
                ("last_name", "Фамилия"),
                ("first_name", "Имя"),
                ("middle_name", "Отчество"),
                ("maiden_name", "Девичья"),
            )
            if nm[key]
        ]
        if name_pairs:
            flag = "есть" if nm["has_karma"] else "нет"
            _section(flow, s, "Число и карма имени")
            flow.append(_kv_table(s, [(k, str(v)) for k, v in name_pairs], cols=4))
            flow.append(
                Paragraph(
                    f"Карма имени: <font color='#A8761F'><b>{_e(nm['karma'])}</b></font> — {flag}",
                    s["body"],
                )
            )

    if "karma_events" in report:
        events = [
            e for e in (report["karma_events"]["first"], report["karma_events"]["second"]) if e
        ]
        if events:
            _section(flow, s, "Кармические события")
            for e in events:
                flow.append(Paragraph(_e(e["text"]), s["interp"]))

    if "days" in report:
        days = report["days"]
        _section(flow, s, "Благоприятные · критические · травмоопасные дни")
        for label, key in (
            ("Благоприятные", "favorable"),
            ("Критические", "critical"),
            ("Травмоопасные", "traumatic"),
        ):
            dates = ", ".join(_fmt_dates(days[key])) or "—"
            flow.append(
                Paragraph(f"<font color='#A8761F'><b>{label}.</b></font> {_e(dates)}", s["interp"])
            )

    if "forecast" in report:
        fc = report["forecast"]
        _section(flow, s, "Прогноз на год" if len(fc) == 1 else f"Прогноз на {len(fc)} лет")
        # «График жизненных сил по годам» (Matr!BE59:BE158) — энергокривая 0..99.
        if "calculations" in report:
            _ensure_fonts()
            flow.append(Paragraph("<b>График жизненных сил по годам</b>", s["interp"]))
            flow.append(life_force_curve(energy_curve(report["calculations"]["life_code"]), _SANS))
        for f in fc:
            sign = "+" if f["year_value"] >= 0 else ""
            head = (
                f"<font name='{_SERIF_B}' size='15' color='#A8761F'>{f['year']}</font> "
                f"<font color='#6B6E84'>возраст {f['age']} · личное число года "
                f"{f['personal_year']} — {_e(f['personal_year_text'])}</font>"
            )
            flow.append(Paragraph(head, s["interp"]))
            flow.append(
                Paragraph(
                    f"Луна {f['moon']} / Солнце {f['sun']} / ИТОГ {sign}{f['year_value']}",
                    s["body"],
                )
            )
            if f.get("energy_potential") is not None:
                trend = _ENERGY_TREND_TEXT.get(f["energy_potential"], "стабильно")
                flow.append(Paragraph(f"<b>Энергетический потенциал.</b> {trend}", s["body"]))
            total = f.get("total_text") or f["year_value_text"]
            if total:
                flow.append(Paragraph(f"<b>Итог года.</b> {_e(_as_text(total))}", s["body"]))
            if f["fate"] == "+" and f.get("rebirth_cycle_text"):
                rc = _e(_as_text(f["rebirth_cycle_text"]))
                flow.append(Paragraph(f"<b>12-летний цикл перерождения.</b> {rc}", s["body"]))
            if f["sun"] == 0 and f.get("sun_text"):
                flow.append(
                    Paragraph(
                        f"<font color='#A8761F'><b>Нулевой период.</b></font> "
                        f"{_e(_as_text(f['sun_text']))}",
                        s["body"],
                    )
                )
            if f.get("life_force_text"):
                flow.append(
                    Paragraph(
                        f"<b>График кода жизни (код {f['life_force_digit']}).</b> "
                        f"{_e(_as_text(f['life_force_text']))}",
                        s["body"],
                    )
                )
            if f["fate"] == "+":
                flow.append(Paragraph("<b>Судьбоносный год.</b>", s["body"]))
            flow.append(Spacer(1, 6))

    if "moon_sun" in report:
        ms = report["moon_sun"]
        pn = ms["personal_numbers"]
        if _want(report, "moon_sun_monthly"):
            years = ms.get("monthly_years") or [{"year": None, "monthly": ms["monthly"]}]
            # «Энергетический график на текущий год» (Matr!CC28:CO28) — помесячная энергия.
            cur_year = years[0].get("year")
            if "calculations" in report and birth_date and cur_year:
                _ensure_fonts()
                me = monthly_energy_year(
                    report["calculations"]["life_code"], birth_date.year, cur_year
                )
                _section(flow, s, "Энергетический график на текущий год")
                flow.append(monthly_energy(me, _SANS))
            if len(years) > 1:
                # Пятилетний прогноз: Луна/Солнце по месяцам на все годы (фидбэк 11.06.2026).
                _section(flow, s, "Луна и Солнце по месяцам · по годам")
                for yb in years:
                    flow.append(
                        Paragraph(
                            f"<font name='{_SERIF_B}' size='13' color='#A8761F'>"
                            f"{yb['year']}</font>",
                            s["interp"],
                        )
                    )
                    for m in yb["monthly"]:
                        flow.append(
                            Paragraph(f"<b>{_e(m['month_name'])}.</b> {_e(m['text'])}", s["interp"])
                        )
            else:
                _section(flow, s, "Луна и Солнце по месяцам")
                for m in years[0]["monthly"]:
                    flow.append(
                        Paragraph(f"<b>{_e(m['month_name'])}.</b> {_e(m['text'])}", s["interp"])
                    )
        if _want(report, "personal_year"):
            _section(flow, s, "Персональное число года")
            flow.append(
                Paragraph(
                    f"<font name='{_SERIF_B}' size='15' color='#A8761F'>"
                    f"{pn['personal_year']}</font>",
                    s["interp"],
                )
            )
            for para in _as_text(pn["personal_year_text"]).split("\n"):
                if para.strip():
                    flow.append(Paragraph(_e(para.strip()), s["body"]))
        if _want(report, "personal_numbers"):
            _section(flow, s, "Личные числа месяца и дня · на дату отчёта")
            flow.append(
                _kv_table(
                    s,
                    [
                        ("Месяц", str(pn["personal_month"])),
                        ("День", str(pn["personal_day"])),
                    ],
                    cols=2,
                )
            )
            if pn["combo_title"]:
                flow.append(Paragraph(f"<b>{_e(pn['combo_title'])}</b>", s["interp"]))
                flow.append(Paragraph(_e(pn["combo_text"]), s["body"]))
            if pn["personal_month_text"]:
                flow.append(
                    Paragraph(f"<b>Месяц.</b> {_e(pn['personal_month_text'])}", s["interp"])
                )
            if pn["personal_day_text"]:
                flow.append(Paragraph(f"<b>День.</b> {_e(pn['personal_day_text'])}", s["interp"]))

    buf = BytesIO()
    doc = BaseDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=_L,
        rightMargin=_R,
        topMargin=_T,
        bottomMargin=_B,
        title="Нумерологическая матрица",
        author="Нумерологическая матрица",
    )
    frame = Frame(_L, _B, _CW, A4[1] - _T - _B, id="main")

    def _paint(canvas, doc_, *, footer: bool) -> None:
        canvas.saveState()
        canvas.setFillColor(PAPER)
        canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
        if footer:
            canvas.setStrokeColor(RULE)
            canvas.setLineWidth(0.5)
            canvas.line(_L, 13 * mm, A4[0] - _R, 13 * mm)
            canvas.setFont(_SANS, 8)
            canvas.setFillColor(MUTED)
            canvas.drawString(_L, 9 * mm, full_name)
            canvas.setFont(_SERIF, 8)
            canvas.drawRightString(A4[0] - _R, 9 * mm, str(doc_.page))
        canvas.restoreState()

    doc.addPageTemplates(
        [
            PageTemplate(
                id="cover", frames=[frame], onPage=lambda c, d: _paint(c, d, footer=False)
            ),
            PageTemplate(id="body", frames=[frame], onPage=lambda c, d: _paint(c, d, footer=True)),
        ]
    )
    # первая страница — cover (без колонтитула), дальше — body
    flow.insert(0, NextPageTemplate("body"))
    doc.build(flow)
    return buf.getvalue()
