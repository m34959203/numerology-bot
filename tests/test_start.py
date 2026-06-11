"""bot.handlers.start: /start (+ создание пользователя), навигация по меню."""

from __future__ import annotations

from bot import texts
from bot.handlers import start
from core import repositories as repo
from tests.conftest import fake_message, fake_query


async def test_start_greets_and_registers_user(test_db):
    msg = fake_message("/start", user_id=777, full_name="Новый Гость")
    await start.cmd_start(msg)

    msg.answer.assert_awaited_once()
    assert msg.answer.await_args.args[0] == texts.START
    # пользователь записан в БД
    async with test_db() as s:
        user = await repo.get_or_create_user(s, telegram_id=777, name="Новый Гость")
        assert user.id is not None


async def test_start_idempotent_for_existing_user(test_db):
    async with test_db() as s:
        first = await repo.get_or_create_user(s, telegram_id=777, name="Гость")
        await s.commit()
        first_id = first.id

    await start.cmd_start(fake_message("/start", user_id=777, full_name="Гость"))

    async with test_db() as s:
        again = await repo.get_or_create_user(s, telegram_id=777, name="Гость")
        assert again.id == first_id  # дубля нет


async def test_main_menu_navigation(test_db):
    q = fake_query("menu:main")
    await start.cb_main(q)
    q.message.edit_text.assert_awaited_once()
    assert q.message.edit_text.await_args.args[0] == texts.START
    q.answer.assert_awaited_once()


async def test_help_navigation(test_db):
    q = fake_query("menu:help")
    await start.cb_help(q)
    q.message.edit_text.assert_awaited_once()
    assert q.message.edit_text.await_args.args[0] == texts.HELP
    q.answer.assert_awaited_once()
