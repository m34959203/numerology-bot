"""Операции с БД. Идемпотентность платежей: один charge_id = одна выдача."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import Order, Payment, Result, Service, SurveyData, User


def _now() -> datetime:
    return datetime.now(UTC)


async def get_or_create_user(session: AsyncSession, telegram_id: int, name: str | None) -> User:
    user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
    if user is None:
        user = User(telegram_id=telegram_id, name=name, created_at=_now())
        session.add(user)
        await session.flush()
    return user


async def list_active_services(session: AsyncSession) -> list[Service]:
    return list(await session.scalars(select(Service).where(Service.is_active.is_(True))))


async def get_service(session: AsyncSession, service_id: int) -> Service | None:
    return await session.get(Service, service_id)


async def create_order(session: AsyncSession, user_id: int, service_id: int) -> Order:
    order = Order(user_id=user_id, service_id=service_id, status="created", created_at=_now())
    session.add(order)
    await session.flush()
    return order


async def payment_exists(session: AsyncSession, charge_id: str) -> bool:
    return (
        await session.scalar(
            select(Payment.id).where(Payment.telegram_payment_charge_id == charge_id)
        )
    ) is not None


async def record_payment(
    session: AsyncSession, order_id: int, charge_id: str, amount_stars: int
) -> Payment | None:
    """Записать платёж. Если charge_id уже есть — None (защита от двойной выдачи)."""
    if await payment_exists(session, charge_id):
        return None
    payment = Payment(
        order_id=order_id,
        telegram_payment_charge_id=charge_id,
        amount_stars=amount_stars,
        status="paid",
        created_at=_now(),
    )
    session.add(payment)
    await session.flush()
    return payment


async def save_survey(session: AsyncSession, order_id: int, **fields) -> SurveyData:
    survey = SurveyData(order_id=order_id, **fields)
    session.add(survey)
    await session.flush()
    return survey


async def save_result(session: AsyncSession, order_id: int, payload: str) -> Result:
    result = Result(order_id=order_id, payload=payload, created_at=_now())
    session.add(result)
    await session.flush()
    return result


async def get_survey(session: AsyncSession, order_id: int) -> SurveyData | None:
    return await session.scalar(select(SurveyData).where(SurveyData.order_id == order_id))


async def get_result(session: AsyncSession, result_id: int) -> Result | None:
    return await session.get(Result, result_id)


async def list_results(session: AsyncSession, user_id: int) -> list[Result]:
    stmt = (
        select(Result)
        .join(Order, Result.order_id == Order.id)
        .where(Order.user_id == user_id)
        .order_by(Result.created_at.desc())
    )
    return list(await session.scalars(stmt))


async def mark_refunded(session: AsyncSession, charge_id: str) -> bool:
    payment = await session.scalar(
        select(Payment).where(Payment.telegram_payment_charge_id == charge_id)
    )
    if payment is None or payment.status == "refunded":
        return False
    payment.status = "refunded"
    payment.refunded_at = _now()
    return True


async def seed_services(session: AsyncSession, services: list[dict]) -> int:
    """Синхронизировать каталог с переданным списком (по code).

    Существующие услуги обновляются (title/description/цены, is_active=True),
    отсутствующие в списке — деактивируются (is_active=False), новые — создаются.
    Возвращает число добавленных.
    """
    added = 0
    wanted_codes = {spec["code"] for spec in services}
    for spec in services:
        service = await session.scalar(select(Service).where(Service.code == spec["code"]))
        if service is None:
            session.add(Service(**spec, is_active=True))
            added += 1
        else:
            for field, value in spec.items():
                setattr(service, field, value)
            service.is_active = True
    # Услуги вне нового каталога убираем из выдачи (не удаляем — ради истории заказов).
    stale = await session.scalars(
        select(Service).where(Service.is_active.is_(True), Service.code.not_in(wanted_codes))
    )
    for service in stale:
        service.is_active = False
    return added
