"""Генерация PDF-отчёта (reportlab) с поддержкой кириллицы.

Шрифт DejaVuSans ищется по системным путям или по settings.pdf_font_path.
В Docker добавить шрифты: apt-get install fonts-dejavu-core (или смонтировать TTF).

Экранируется ТОЛЬКО динамический текст (трактовки/имена) — структурные теги
reportlab (<b>, <br/>) остаются рабочими.
"""

from __future__ import annotations

from datetime import date
from io import BytesIO
from pathlib import Path

from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from bot.config import settings
from core.render import _fmt_dates, _val

_FONT = "DejaVuSans"
_FONT_BOLD = "DejaVuSans-Bold"
_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
]
_BOLD_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
]
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
_fonts_ready = False


def _find_font(candidates: list[str], override: str = "") -> str | None:
    if override and Path(override).exists():
        return override
    for path in candidates:
        if Path(path).exists():
            return path
    return None


def _ensure_fonts() -> None:
    global _fonts_ready
    if _fonts_ready:
        return
    regular = _find_font(_FONT_CANDIDATES, settings.pdf_font_path)
    if regular is None:
        raise RuntimeError(
            "Не найден TTF-шрифт с кириллицей. Установите fonts-dejavu-core "
            "или задайте PDF_FONT_PATH."
        )
    pdfmetrics.registerFont(TTFont(_FONT, regular))
    bold = _find_font(_BOLD_CANDIDATES)
    pdfmetrics.registerFont(TTFont(_FONT_BOLD, bold or regular))
    _fonts_ready = True


def _styles():
    base = ParagraphStyle("base", fontName=_FONT, fontSize=10, leading=14, alignment=TA_LEFT)
    return {
        "title": ParagraphStyle("title", parent=base, fontName=_FONT_BOLD, fontSize=16, leading=20),
        "sub": ParagraphStyle("sub", parent=base, fontSize=11, leading=15),
        "h": ParagraphStyle(
            "h",
            parent=base,
            fontName=_FONT_BOLD,
            fontSize=13,
            leading=18,
            spaceBefore=10,
            spaceAfter=4,
        ),
        "p": base,
        "small": ParagraphStyle("small", parent=base, fontSize=9, leading=12),
    }


def _e(value) -> str:
    """Экранировать динамический текст для разметки reportlab Paragraph."""
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_report_pdf(report: dict, full_name: str, birth_date: date | None) -> bytes:
    """Собрать PDF-отчёт из структуры build_report. Возвращает bytes."""
    _ensure_fonts()
    s = _styles()

    flow = []
    born = f", р. {birth_date.strftime('%d.%m.%Y')}" if birth_date else ""
    flow.append(Paragraph("Нумерологическая матрица", s["title"]))
    flow.append(Paragraph(_e(f"{full_name}{born}"), s["sub"]))

    # Рендерим только присутствующие секции — состав зависит от тарифа
    # (см. core.numerology.tariffs).
    if "calculations" in report:
        c = report["calculations"]
        danger = c["danger_age"] if c["danger_age"] is not None else "нет"
        flow.append(Paragraph("Исходные данные и вычисления", s["h"]))
        flow.append(
            Paragraph(
                f"Полных лет: {c['full_years']} · Прожито дней: {c['lived_days']} · "
                f"Жизнь: {c['life_task']} · Духовный уровень: {c['spiritual_level']}<br/>"
                f"Код человека: {_e(c['human_code'])} · Код жизни: {_e(c['life_code'])} · "
                f"Финансовый код: {_e(c['finance_code'])} · "
                f"Счастливые числа: {_e(c['lucky_numbers'])}<br/>"
                f"Доступ к деньгам: {c['money_access']} · Жизненные силы: {c['vitality']} · "
                f"Опасный возраст: {danger}",
                s["p"],
            )
        )

    if "psychomatrix" in report:
        pm = report["psychomatrix"]
        q = {row["label"]: row for row in pm["qualities"]}
        sc = {row["label"]: row for row in pm["scalars"]}
        flow.append(Paragraph("Психоматрица", s["h"]))
        grid = " · ".join(f"{_e(lbl)}: {_val(q[lbl]['value'])}" for lbl in _PSYCHO_ORDER)
        flow.append(Paragraph(grid, s["p"]))
        flow.append(
            Paragraph(
                f"Число души: {sc['Число души']['value']} · "
                f"ЧЖП: {sc['Число жизненного пути (ЧЖП)']['value']} · "
                f"Уровень сознания: {sc['Уровень сознания']['value']} · "
                f"Код поведения: {_e(sc['Код поведения']['value'])}",
                s["small"],
            )
        )
        flow.append(Spacer(1, 4))
        for lbl in _PSYCHO_ORDER:
            text = q[lbl]["text"]
            if text:
                flow.append(
                    Paragraph(f"<b>{_e(lbl)}</b> ({_val(q[lbl]['value'])}): {_e(text)}", s["p"])
                )

    if "name" in report:
        nm = report["name"]
        name_parts = [
            f"{label}: {_e(nm[key])}"
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
            flow.append(Paragraph("Число и карма имени", s["h"]))
            flow.append(
                Paragraph(
                    " · ".join(name_parts) + f"<br/>Карма имени: {nm['karma']} — {flag}", s["p"]
                )
            )

    if "karma_events" in report:
        events = [
            e for e in (report["karma_events"]["first"], report["karma_events"]["second"]) if e
        ]
        if events:
            flow.append(Paragraph("Кармические события", s["h"]))
            for e in events:
                flow.append(Paragraph(_e(e["text"]), s["p"]))

    if "days" in report:
        days = report["days"]
        flow.append(Paragraph("Благоприятные / критические / травмоопасные дни", s["h"]))
        flow.append(
            Paragraph(
                f"Благоприятные: {', '.join(_fmt_dates(days['favorable']))}<br/>"
                f"Критические: {', '.join(_fmt_dates(days['critical'])) or '—'}<br/>"
                f"Травмоопасные: {', '.join(_fmt_dates(days['traumatic']))}",
                s["p"],
            )
        )

    if "forecast" in report:
        fc = report["forecast"]
        flow.append(
            Paragraph("Прогноз на год" if len(fc) == 1 else f"Прогноз на {len(fc)} лет", s["h"])
        )
        for f in fc:
            cyc = (
                f"; 12-цикл: {_e(f['rebirth_cycle_text'])}"
                if f["fate"] == "+" and f["rebirth_cycle_text"]
                else ""
            )
            sign = "+" if f["year_value"] >= 0 else ""
            flow.append(
                Paragraph(
                    f"<b>{f['year']} (возраст {f['age']})</b>: {f['personal_year']} — "
                    f"{_e(f['personal_year_text'])}; Луна {f['moon']} / Солнце {f['sun']}; "
                    f"год {sign}{f['year_value']} — {_e(f['year_value_text'])}; "
                    f"судьбоносный: {f['fate']}{cyc}",
                    s["p"],
                )
            )

    if "moon_sun" in report:
        ms = report["moon_sun"]
        pn = ms["personal_numbers"]
        flow.append(Paragraph("Луна и Солнце по месяцам", s["h"]))
        for m in ms["monthly"]:
            flow.append(Paragraph(f"<b>{_e(m['month_name'])}</b>: {_e(m['text'])}", s["p"]))

        flow.append(Paragraph("Личные числа (на дату отчёта)", s["h"]))
        flow.append(
            Paragraph(
                f"Год: {pn['personal_year']} · Месяц: {pn['personal_month']} · "
                f"День: {pn['personal_day']}",
                s["p"],
            )
        )
        if pn["combo_title"]:
            flow.append(Paragraph(f"<b>{_e(pn['combo_title'])}</b>", s["p"]))
            flow.append(Paragraph(_e(pn["combo_text"]), s["p"]))
        if pn["personal_month_text"]:
            flow.append(Paragraph(f"Месяц: {_e(pn['personal_month_text'])}", s["p"]))
        if pn["personal_day_text"]:
            flow.append(Paragraph(f"День: {_e(pn['personal_day_text'])}", s["p"]))

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="Нумерологическая матрица",
    )
    doc.build(flow)
    return buf.getvalue()
