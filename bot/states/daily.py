"""FSM-состояния прогноза на день (на выбранную дату)."""

from aiogram.fsm.state import State, StatesGroup


class DailyStates(StatesGroup):
    birth_date = State()  # дата рождения (ДД.ММ.ГГГГ)
    target_date = State()  # дата прогноза (ДД.ММ.ГГГГ или «Сегодня»)
