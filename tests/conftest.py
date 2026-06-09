"""Общие фикстуры для тестов Telegram-слоя.

- test_db: подменяет фабрику сессий core.db на общий in-memory SQLite (StaticPool,
  чтобы данные жили между вызовами session_scope), создаёт таблицы.
- фейковые Message / CallbackQuery (unittest.mock) и реальный FSMContext
  (MemoryStorage) — хендлеры зовём напрямую, без сети Telegram.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from core.models import Base


@pytest.fixture
async def test_db(monkeypatch):
    """Общий in-memory SQLite, подставленный в core.db.session_scope."""
    import core.db as db

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    monkeypatch.setattr(db, "_engine", engine)
    monkeypatch.setattr(db, "_session_factory", factory)
    yield factory
    await engine.dispose()


def fake_message(text: str | None = None, *, user_id: int = 1, full_name: str = "Тест", **extra):
    m = MagicMock(name="Message")
    m.text = text
    m.from_user = SimpleNamespace(id=user_id, full_name=full_name)
    m.successful_payment = extra.get("successful_payment")
    m.answer = AsyncMock(name="answer")
    m.answer_document = AsyncMock(name="answer_document")
    m.answer_invoice = AsyncMock(name="answer_invoice")
    m.edit_text = AsyncMock(name="edit_text")
    return m


def fake_query(data: str | None = None, *, user_id: int = 1, full_name: str = "Тест", message=None):
    q = MagicMock(name="CallbackQuery")
    q.data = data
    q.from_user = SimpleNamespace(id=user_id, full_name=full_name)
    q.message = message or fake_message(user_id=user_id, full_name=full_name)
    q.answer = AsyncMock(name="cq.answer")
    return q


def make_state(user_id: int = 1) -> FSMContext:
    return FSMContext(
        storage=MemoryStorage(),
        key=StorageKey(bot_id=1, chat_id=user_id, user_id=user_id),
    )
