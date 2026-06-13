"""FSM-анкета: ФИО + дата рождения (+ родители и девичья фамилия по тарифу)
→ подтверждение → расчёт и выдача.

Состав доп. шагов зависит от тарифа (см. core.numerology.tariffs):
- даты рождения матери и отца — если тариф включает секцию «karma_events»
  (кармические события BG17/BG20 считаются из дат родителей);
- пол и девичья фамилия — если тариф включает «name» (число имени); девичья
  фамилия спрашивается только у женщин. Все доп. поля опциональны («Пропустить»).

Запускается после успешной оплаты (см. payment.py).
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, date, datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot import keyboards
from bot.config import settings
from bot.delivery import deliver_report
from bot.states.survey import SurveyStates
from core.db import session_scope
from core.i18n import t
from core.numerology import PersonInput
from core.numerology.tariffs import report_for, spec_for
from core.repositories import save_result, save_survey
from core.validators import ValidationError, parse_birth_date, validate_name

logger = logging.getLogger(__name__)
router = Router(name="survey")


def _flags(data: dict) -> tuple[bool, bool]:
    """(нужны даты родителей, нужны пол+девичья) — по требованиям тарифа."""
    spec = spec_for(data.get("service_code"))
    return spec.needs_parents, spec.needs_name


def _parents_required(data: dict) -> bool:
    """Даты родителей обязательны для тарифа (без «Пропустить»)."""
    return spec_for(data.get("service_code")).parents_required


def _parents_kb(data: dict):
    """Клавиатура шага родителей: скрываем «Пропустить», если даты обязательны."""
    return None if _parents_required(data) else keyboards.skip_kb(_loc(data))


def _loc(data: dict) -> str:
    """Локаль анкеты (заложена в state при старте, см. catalog/payment)."""
    return data.get("locale", "ru")


def _opt_date(iso: str | None) -> date | None:
    return date.fromisoformat(iso) if iso else None


async def begin_survey(
    message: Message,
    state: FSMContext,
    *,
    order_id: int,
    charge_id: str,
    service_code: str,
    service_title: str,
    locale: str,
) -> None:
    """Запустить FSM-анкету после оплаты (Stars/имитация/TON) — единая точка.

    Кладёт в state идентификаторы заказа + локаль и спрашивает первое поле."""
    await state.set_state(SurveyStates.last_name)
    await state.update_data(
        order_id=order_id,
        charge_id=charge_id,
        service_code=service_code,
        service_title=service_title,
        locale=locale,
    )
    await message.answer(t("ui.ask_last_name", locale))


async def _notify_master(
    bot,
    *,
    order_id: int,
    service_title: str,
    client_id: int,
    client_name: str,
    client_username: str | None,
) -> None:
    """Сообщить мастеру (MASTER_CHAT_ID, иначе ADMIN_IDS) об оплаченном ручном тарифе."""
    handle = f"@{client_username}" if client_username else f"id {client_id}"
    text = (
        "🔔 Оплачен ручной тариф — нужна ваша подготовка.\n"
        f"Заказ #{order_id}: {service_title}\n"
        f"Клиент: {client_name} ({handle})\n"
        f"Свяжитесь с клиентом для уточнения данных и выдачи разбора."
    )
    for chat_id in settings.master_chat_id_list:
        try:
            await bot.send_message(chat_id, text)
        except Exception:
            logger.exception("Не удалось уведомить мастера chat_id=%s", chat_id)


async def deliver_after_payment(
    message: Message,
    state: FSMContext,
    *,
    client_id: int,
    client_name: str,
    client_username: str | None,
    order_id: int,
    charge_id: str,
    service_code: str,
    service_title: str,
    locale: str,
    success_key: str = "ui.pay_success",
) -> None:
    """Единый постоплатный шаг (Stars/имитация/TON).

    Ручной тариф (spec.manual) — авто-расчёта нет: подтверждаем клиенту и зовём
    мастера, анкета НЕ запускается. Авто-тариф — обычный поток «оплата → анкета».
    """
    if spec_for(service_code).manual:
        await message.answer(t("ui.pay_success_manual", locale))
        await _notify_master(
            message.bot,
            order_id=order_id,
            service_title=service_title,
            client_id=client_id,
            client_name=client_name,
            client_username=client_username,
        )
        return
    await message.answer(t(success_key, locale))
    await begin_survey(
        message,
        state,
        order_id=order_id,
        charge_id=charge_id,
        service_code=service_code,
        service_title=service_title,
        locale=locale,
    )


def _summary(data: dict) -> str:
    """Сводка для подтверждения — показываем только заполненные поля."""
    loc = _loc(data)
    gender = t("lbl.gender_female", loc) if data.get("gender") == "f" else t("lbl.gender_male", loc)
    lines = [
        t("ui.confirm_header", loc),
        f"{t('lbl.last_name', loc)}: {data['last_name']}",
        f"{t('lbl.first_name', loc)}: {data['first_name']}",
        f"{t('lbl.middle_name', loc)}: {data['middle_name']}",
        f"{t('ui.label_birth_date', loc)}: {_opt_date(data['birth_date']).strftime('%d.%m.%Y')}",
    ]
    if data.get("gender"):
        lines.append(f"{t('ui.label_gender', loc)}: {gender}")
    if data.get("maiden_name"):
        lines.append(f"{t('lbl.maiden_name', loc)}: {data['maiden_name']}")
    if data.get("mother_birth_date"):
        md = _opt_date(data["mother_birth_date"]).strftime("%d.%m.%Y")
        lines.append(f"{t('ui.label_mother_bd', loc)}: {md}")
    if data.get("father_birth_date"):
        fd = _opt_date(data["father_birth_date"]).strftime("%d.%m.%Y")
        lines.append(f"{t('ui.label_father_bd', loc)}: {fd}")
    return "\n".join(lines) + t("ui.confirm_footer", loc)


async def _to_confirm(message: Message, state: FSMContext) -> None:
    await state.set_state(SurveyStates.confirm)
    data = await state.get_data()
    await message.answer(
        _summary(data), reply_markup=keyboards.confirm_kb(_loc(data)), parse_mode=None
    )


async def _ask_gender(message: Message, state: FSMContext) -> None:
    await state.set_state(SurveyStates.gender)
    loc = _loc(await state.get_data())
    await message.answer(
        t("ui.ask_gender", loc), reply_markup=keyboards.gender_kb(loc), parse_mode=None
    )


async def _after_basics(message: Message, state: FSMContext) -> None:
    """После даты рождения: родители → пол/девичья → подтверждение (по тарифу)."""
    data = await state.get_data()
    loc = _loc(data)
    needs_parents, needs_name = _flags(data)
    if needs_parents:
        await state.set_state(SurveyStates.mother_birth_date)
        await message.answer(
            t("ui.ask_mother_bd", loc), reply_markup=_parents_kb(data), parse_mode=None
        )
    elif needs_name:
        await _ask_gender(message, state)
    else:
        await _to_confirm(message, state)


async def _after_parents(message: Message, state: FSMContext) -> None:
    """После дат родителей: пол/девичья (если тариф с именем) → подтверждение."""
    _, needs_name = _flags(await state.get_data())
    if needs_name:
        await _ask_gender(message, state)
    else:
        await _to_confirm(message, state)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    if await state.get_state() is None:
        return
    loc = _loc(await state.get_data())
    await state.clear()
    await message.answer(t("ui.survey_cancelled", loc), parse_mode=None)


async def _name_step(message, state, field_key, save_key, next_state, next_prompt) -> None:
    data = await state.get_data()
    loc = _loc(data)
    try:
        value = validate_name(message.text, t(field_key, loc), loc)
    except ValidationError as e:
        await message.answer(str(e), parse_mode=None)
        return
    await state.update_data(**{save_key: value})
    await state.set_state(next_state)
    await message.answer(t(next_prompt, loc))


@router.message(SurveyStates.last_name, F.text)
async def step_last_name(message: Message, state: FSMContext) -> None:
    await _name_step(
        message, state, "lbl.last_name", "last_name", SurveyStates.first_name, "ui.ask_first_name"
    )


@router.message(SurveyStates.first_name, F.text)
async def step_first_name(message: Message, state: FSMContext) -> None:
    await _name_step(
        message,
        state,
        "lbl.first_name",
        "first_name",
        SurveyStates.middle_name,
        "ui.ask_middle_name",
    )


@router.message(SurveyStates.middle_name, F.text)
async def step_middle_name(message: Message, state: FSMContext) -> None:
    await _name_step(
        message,
        state,
        "lbl.middle_name",
        "middle_name",
        SurveyStates.birth_date,
        "ui.ask_birth_date",
    )


@router.message(SurveyStates.birth_date, F.text)
async def step_birth_date(message: Message, state: FSMContext) -> None:
    loc = _loc(await state.get_data())
    try:
        bd = parse_birth_date(message.text, loc)
    except ValidationError as e:
        await message.answer(str(e), parse_mode=None)
        return
    await state.update_data(birth_date=bd.isoformat())
    await _after_basics(message, state)


@router.message(SurveyStates.mother_birth_date, F.text)
async def step_mother_birth_date(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    loc = _loc(data)
    try:
        bd = parse_birth_date(message.text, loc)
    except ValidationError as e:
        await message.answer(str(e), parse_mode=None)
        return
    await state.update_data(mother_birth_date=bd.isoformat())
    await state.set_state(SurveyStates.father_birth_date)
    await message.answer(
        t("ui.ask_father_bd", loc), reply_markup=_parents_kb(data), parse_mode=None
    )


@router.callback_query(SurveyStates.mother_birth_date, F.data == "survey:skip")
async def skip_mother(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    data = await state.get_data()
    loc = _loc(data)
    if _parents_required(data):  # обязательный тариф: «Пропустить» недопустим
        await query.message.answer(t("ui.ask_mother_bd", loc), parse_mode=None)
        return
    await state.set_state(SurveyStates.father_birth_date)
    await query.message.answer(
        t("ui.ask_father_bd", loc), reply_markup=_parents_kb(data), parse_mode=None
    )


@router.message(SurveyStates.father_birth_date, F.text)
async def step_father_birth_date(message: Message, state: FSMContext) -> None:
    loc = _loc(await state.get_data())
    try:
        bd = parse_birth_date(message.text, loc)
    except ValidationError as e:
        await message.answer(str(e), parse_mode=None)
        return
    await state.update_data(father_birth_date=bd.isoformat())
    await _after_parents(message, state)


@router.callback_query(SurveyStates.father_birth_date, F.data == "survey:skip")
async def skip_father(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    data = await state.get_data()
    if _parents_required(data):  # обязательный тариф: «Пропустить» недопустим
        await query.message.answer(t("ui.ask_father_bd", _loc(data)), parse_mode=None)
        return
    await _after_parents(query.message, state)


@router.callback_query(SurveyStates.gender, F.data.startswith("survey:gender:"))
async def cb_gender(query: CallbackQuery, state: FSMContext) -> None:
    gender = query.data.rsplit(":", 1)[1]  # "f" | "m"
    await state.update_data(gender=gender)
    await query.answer()
    loc = _loc(await state.get_data())
    if gender == "f":
        await state.set_state(SurveyStates.maiden_name)
        await query.message.answer(
            t("ui.ask_maiden_name", loc), reply_markup=keyboards.skip_kb(loc), parse_mode=None
        )
    else:
        await _to_confirm(query.message, state)


@router.message(SurveyStates.gender, F.text)
async def gender_text_fallback(message: Message, state: FSMContext) -> None:
    loc = _loc(await state.get_data())
    await message.answer(
        t("ui.ask_gender", loc), reply_markup=keyboards.gender_kb(loc), parse_mode=None
    )


@router.message(SurveyStates.maiden_name, F.text)
async def step_maiden_name(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    loc = _loc(data)
    try:
        value = validate_name(message.text, t("lbl.maiden_name", loc), loc)
    except ValidationError as e:
        await message.answer(str(e), parse_mode=None)
        return
    await state.update_data(maiden_name=value)
    await _to_confirm(message, state)


@router.callback_query(SurveyStates.maiden_name, F.data == "survey:skip")
async def skip_maiden(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    await _to_confirm(query.message, state)


@router.callback_query(SurveyStates.confirm, F.data == "survey:restart")
async def cb_restart(query: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    keep = {
        k: data[k]
        for k in ("order_id", "charge_id", "service_code", "service_title", "locale")
        if k in data
    }
    await state.set_state(SurveyStates.last_name)
    await state.set_data(keep)
    await query.message.answer(t("ui.ask_last_name", _loc(keep)))
    await query.answer()


@router.callback_query(SurveyStates.confirm, F.data == "survey:confirm")
async def cb_confirm(query: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    locale = _loc(data)
    await query.answer()
    await query.message.answer(t("ui.calculating", locale), parse_mode=None)
    order_id = data["order_id"]

    # Этап 1 — расчёт и сохранение. При сбое остаёмся в confirm: пользователь
    # может повторить тем же «Всё верно» (данные анкеты не теряются).
    try:
        person = PersonInput(
            last_name=data["last_name"],
            first_name=data["first_name"],
            middle_name=data["middle_name"],
            birth_date=date.fromisoformat(data["birth_date"]),
            mother_birth_date=_opt_date(data.get("mother_birth_date")),
            father_birth_date=_opt_date(data.get("father_birth_date")),
            maiden_name=data.get("maiden_name") or None,
        )
        reference = datetime.now(UTC).date()
        report = report_for(person, reference, data.get("service_code"), locale)
        full_name = f"{person.last_name} {person.first_name} {person.middle_name}"
        async with session_scope() as session:
            await save_survey(
                session,
                order_id,
                last_name=person.last_name,
                first_name=person.first_name,
                middle_name=person.middle_name,
                birth_date=person.birth_date,
                mother_birth_date=person.mother_birth_date,
                father_birth_date=person.father_birth_date,
                maiden_name=person.maiden_name,
            )
            await save_result(session, order_id, json.dumps(report, ensure_ascii=False))
    except Exception:
        logger.exception("Сбой расчёта/сохранения order_id=%s", order_id)
        await query.message.answer(
            t("ui.calc_error", locale), reply_markup=keyboards.confirm_kb(locale), parse_mode=None
        )
        return

    # Этап 2 — выдача. Отчёт уже сохранён, поэтому при сбое отправки чистим
    # анкету и отсылаем за ним в «Мои расчёты».
    try:
        await deliver_report(query.message, report, full_name, person.birth_date, locale)
    except Exception:
        logger.exception("Сбой выдачи order_id=%s", order_id)
        await state.clear()
        await query.message.answer(
            t("ui.deliver_error", locale),
            reply_markup=keyboards.to_menu_kb(locale),
            parse_mode=None,
        )
        return

    await state.clear()
    await query.message.answer(
        t("ui.delivered", locale), reply_markup=keyboards.to_menu_kb(locale), parse_mode=None
    )
    logger.info("Выдан расчёт order_id=%s", order_id)
