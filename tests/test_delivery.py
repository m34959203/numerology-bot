"""bot.delivery.deliver_report: выбор формата text/pdf/both и fallback PDF→текст."""

from __future__ import annotations

import pytest

from bot import delivery
from bot.config import settings
from tests.conftest import fake_message


@pytest.fixture(autouse=True)
def _stub_render(monkeypatch):
    # render_report и split_message не зависят от реального отчёта в этих тестах.
    monkeypatch.setattr(delivery, "render_report", lambda *a, **k: "ТЕКСТ-ОТЧЁТ")
    monkeypatch.setattr(delivery, "split_message", lambda t: [t])


async def _deliver(fmt: str, monkeypatch, *, pdf_ok: bool = True):
    monkeypatch.setattr(settings, "report_format", fmt)

    def _build(*a, **k):
        if not pdf_ok:
            raise RuntimeError("pdf сломался")
        return b"%PDF-1.4 fake"

    monkeypatch.setattr("core.pdf.build_report_pdf", _build)
    msg = fake_message()
    await delivery.deliver_report(msg, {}, "Ерофеева Юлия", None)
    return msg


async def test_pdf_only(monkeypatch):
    msg = await _deliver("pdf", monkeypatch)
    msg.answer_document.assert_awaited_once()
    msg.answer.assert_not_awaited()


async def test_text_only(monkeypatch):
    msg = await _deliver("text", monkeypatch)
    msg.answer.assert_awaited_once()
    assert msg.answer.await_args.args[0] == "ТЕКСТ-ОТЧЁТ"
    msg.answer_document.assert_not_awaited()


async def test_both(monkeypatch):
    msg = await _deliver("both", monkeypatch)
    msg.answer_document.assert_awaited_once()
    msg.answer.assert_awaited_once()


async def test_pdf_failure_falls_back_to_text(monkeypatch):
    msg = await _deliver("pdf", monkeypatch, pdf_ok=False)
    # PDF упал до отправки документа → ушёл текст как fallback.
    msg.answer_document.assert_not_awaited()
    msg.answer.assert_awaited_once()
    assert msg.answer.await_args.args[0] == "ТЕКСТ-ОТЧЁТ"
