"""Диагностика: получить chat_id чата (для настройки MASTER_CHAT_ID).

`my_chat_member` логирует id чата при добавлении/удалении бота — так узнаём
chat_id приватной группы/канала мастера (инвайт-ссылка для бота не годится,
нужен числовой id). Команда /chatid отвечает id текущего чата.
"""

from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import ChatMemberUpdated, Message

logger = logging.getLogger(__name__)
router = Router(name="diag")


@router.my_chat_member()
async def on_my_chat_member(update: ChatMemberUpdated) -> None:
    """Бота добавили/удалили из чата — логируем id для настройки MASTER_CHAT_ID."""
    chat = update.chat
    status = update.new_chat_member.status
    logger.info(
        "MY_CHAT_MEMBER chat_id=%s type=%s title=%r status=%s",
        chat.id,
        chat.type,
        chat.title or chat.full_name,
        status,
    )


@router.message(Command("chatid"))
async def cmd_chatid(message: Message) -> None:
    """Ответить id текущего чата (для копирования в MASTER_CHAT_ID)."""
    chat = message.chat
    await message.answer(f"chat_id: <code>{chat.id}</code>\nтип: {chat.type}", parse_mode="HTML")
    logger.info("CHATID запрошен chat_id=%s type=%s", chat.id, chat.type)
