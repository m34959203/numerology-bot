"""Идемпотентность платежей и базовые операции репозитория (aiosqlite)."""

from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core import repositories as repo
from core.models import Base


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        yield s
    await engine.dispose()


async def test_payment_idempotent_and_flow(session):
    user = await repo.get_or_create_user(session, telegram_id=555, name="Тест")
    # повторный get_or_create не создаёт дубль
    user2 = await repo.get_or_create_user(session, telegram_id=555, name="Тест")
    assert user.id == user2.id

    await repo.seed_services(
        session,
        [
            {"code": "full_matrix", "title": "Матрица", "description": "...", "price_stars": 100},
        ],
    )
    services = await repo.list_active_services(session)
    assert len(services) == 1
    # повторный сид не дублирует
    assert (
        await repo.seed_services(
            session,
            [
                {
                    "code": "full_matrix",
                    "title": "Матрица",
                    "description": "...",
                    "price_stars": 100,
                },
            ],
        )
        == 0
    )

    order = await repo.create_order(session, user.id, services[0].id)
    p1 = await repo.record_payment(session, order.id, "CHARGE_X", 100)
    assert p1 is not None
    # второй платёж с тем же charge_id -> None (защита от двойной выдачи)
    p2 = await repo.record_payment(session, order.id, "CHARGE_X", 100)
    assert p2 is None

    await repo.save_survey(
        session,
        order.id,
        last_name="Иванов",
        first_name="Иван",
        middle_name="Иванович",
        birth_date=date(1990, 1, 1),
    )
    await repo.save_result(session, order.id, '{"ok": true}')
    results = await repo.list_results(session, user.id)
    assert len(results) == 1

    assert await repo.mark_refunded(session, "CHARGE_X") is True
    # повторный возврат -> False
    assert await repo.mark_refunded(session, "CHARGE_X") is False
