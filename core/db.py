"""Асинхронный доступ к БД (SQLAlchemy 2 + asyncpg)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.config import settings
from core.models import Base

_engine = create_async_engine(settings.database_url, pool_pre_ping=True)
_session_factory = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Контекст транзакции: commit при успехе, rollback при ошибке."""
    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def create_all() -> None:
    """Создать таблицы (для dev/быстрого старта; в проде — Alembic)."""
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
