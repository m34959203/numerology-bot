"""ORM-модели (SQLAlchemy 2). Минимальная схема из ТЗ, раздел 6.

Поля будут уточняться по ходу этапов. TIMESTAMP — всегда with timezone.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(255))
    locale: Mapped[str] = mapped_column(String(8), default="ru", server_default="ru")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    # Цена в тенге — основная валюта прайса. price_stars оставлен для будущей
    # оплаты через Telegram Stars (сейчас отключена, см. settings.payment_imitation).
    price_tenge: Mapped[int] = mapped_column(Integer, default=0)
    price_stars: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"))
    status: Mapped[str] = mapped_column(String(32), default="created")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    payment: Mapped[Payment | None] = relationship(back_populates="order")
    survey: Mapped[SurveyData | None] = relationship(back_populates="order")
    result: Mapped[Result | None] = relationship(back_populates="order")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    # Уникален -> идемпотентность: один платёж = одна выдача.
    telegram_payment_charge_id: Mapped[str] = mapped_column(String(255), unique=True)
    amount_stars: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32), default="paid")  # paid | refunded
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    order: Mapped[Order] = relationship(back_populates="payment")


class SurveyData(Base):
    __tablename__ = "survey_data"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    last_name: Mapped[str] = mapped_column(String(255))
    first_name: Mapped[str] = mapped_column(String(255))
    middle_name: Mapped[str | None] = mapped_column(String(255))
    birth_date: Mapped[date] = mapped_column()
    mother_birth_date: Mapped[date | None] = mapped_column()
    father_birth_date: Mapped[date | None] = mapped_column()
    maiden_name: Mapped[str | None] = mapped_column(String(255))

    order: Mapped[Order] = relationship(back_populates="survey")


class Result(Base):
    __tablename__ = "results"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    payload: Mapped[str] = mapped_column(Text)  # структурированный отчёт (JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    order: Mapped[Order] = relationship(back_populates="result")
