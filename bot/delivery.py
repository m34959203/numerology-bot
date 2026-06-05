"""Выдача отчёта пользователю в выбранном формате (text / pdf / both)."""

from __future__ import annotations

import logging
from datetime import date

from aiogram.types import BufferedInputFile, Message

from bot.config import settings
from core.render import render_report, split_message

logger = logging.getLogger(__name__)


def _safe_filename(full_name: str) -> str:
    base = full_name.strip().replace(" ", "_") or "matrix"
    return f"matrix_{base}.pdf"


async def deliver_report(
    message: Message, report: dict, full_name: str, birth_date: date | None
) -> None:
    """Отправить отчёт: текст и/или PDF согласно settings.report_format.

    При сбое генерации PDF — graceful fallback на текст.
    """
    fmt = settings.report_format.lower()
    want_text = fmt in ("text", "both")
    want_pdf = fmt in ("pdf", "both")

    if want_pdf:
        try:
            from core.pdf import build_report_pdf

            pdf_bytes = build_report_pdf(report, full_name, birth_date)
            await message.answer_document(
                BufferedInputFile(pdf_bytes, filename=_safe_filename(full_name)),
                caption="Ваша нумерологическая матрица 🔮",
            )
        except Exception:
            logger.exception("Сбой генерации PDF, отправляю текстом")
            want_text = True  # fallback

    if want_text:
        text = render_report(report, full_name, birth_date)
        for chunk in split_message(text):
            await message.answer(chunk)
