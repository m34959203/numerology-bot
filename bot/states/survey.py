"""FSM-состояния анкеты (Этап 1).

Обязательность опциональных полей уточняется в OPEN_QUESTIONS.md.
"""

from aiogram.fsm.state import State, StatesGroup


class SurveyStates(StatesGroup):
    last_name = State()  # фамилия
    first_name = State()  # имя
    middle_name = State()  # отчество
    birth_date = State()  # дата рождения (ДД.ММ.ГГГГ)
    mother_birth_date = State()  # опц.
    father_birth_date = State()  # опц.
    maiden_name = State()  # опц. девичья фамилия
    confirm = State()  # подтверждение введённых данных
