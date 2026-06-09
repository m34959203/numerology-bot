"""FSM-состояния анкеты (Этап 1).

Обязательность опциональных полей уточняется в OPEN_QUESTIONS.md.
"""

from aiogram.fsm.state import State, StatesGroup


class SurveyStates(StatesGroup):
    last_name = State()  # фамилия
    first_name = State()  # имя
    middle_name = State()  # отчество
    birth_date = State()  # дата рождения (ДД.ММ.ГГГГ)
    mother_birth_date = State()  # опц., если тариф с кармическими событиями
    father_birth_date = State()  # опц., если тариф с кармическими событиями
    gender = State()  # пол (гейт девичьей фамилии); в расчёте не участвует
    maiden_name = State()  # опц. девичья фамилия (только для женщин)
    confirm = State()  # подтверждение введённых данных
