"""Демо-прогон расчётного ядра на нескольких пользователях.

Запуск:  python scripts/demo_report.py
Печатает краткую сводку отчёта (без длинных трактовок) для демо-анкет.
Дата отчёта фиксирована для воспроизводимости.
"""

from __future__ import annotations

from datetime import date

from core.numerology import PersonInput
from core.numerology.report import build_report

REFERENCE = date(2026, 6, 6)

DEMO = [
    ("жен", PersonInput("Петрова", "Анна", "Сергеевна", date(1992, 3, 14))),
    ("муж", PersonInput("Соколов", "Дмитрий", "Иванович", date(1985, 11, 2))),
    ("жен", PersonInput("Кузнецова", "Мария", "Андреевна", date(2000, 7, 27))),
    ("муж", PersonInput("Морозов", "Алексей", "Викторович", date(1978, 9, 9))),
    ("жен", PersonInput("Васильева", "Елена", "Олеговна", date(1995, 5, 30))),
]


def _q(v: int) -> str:
    return "нет" if v == 0 else str(v)


def render(gender: str, p: PersonInput) -> str:
    rep = build_report(p, REFERENCE)
    c = rep["calculations"]
    pm = rep["psychomatrix"]
    days = rep["days"]
    ms = rep["moon_sun"]
    pn = ms["personal_numbers"]
    q = {row["label"]: row["value"] for row in pm["qualities"]}
    sc = {row["label"]: row["value"] for row in pm["scalars"]}

    lines = [
        "═" * 70,
        f"{p.last_name} {p.first_name} {p.middle_name}  ({gender})  "
        f"р. {p.birth_date.strftime('%d.%m.%Y')}   отчёт на {REFERENCE.strftime('%d.%m.%Y')}",
        "─" * 70,
        f"Вычисления: полных лет {c['full_years']}, прожито дней {c['lived_days']}, "
        f"жизнь {c['life_task']}, духовный уровень {c['spiritual_level']}",
        f"  код человека {c['human_code']}, код жизни {c['life_code']}, "
        f"фин-код {c['finance_code']}, счастливые {c['lucky_numbers']}",
        f"  доступ к деньгам {c['money_access']}, жизненные силы {c['vitality']}, "
        f"опасный возраст {c['danger_age'] if c['danger_age'] is not None else 'нет'}",
        "Психоматрица:",
        f"  Характер {_q(q['Характер'])}  Энергия {_q(q['Энергия'])}  "
        f"Интерес {_q(q['Интерес'])}  Здоровье {_q(q['Здоровье'])}  "
        f"Логика {_q(q['Логика, интуиция'])}",
        f"  Труд {_q(q['Труд, власть'])}  Везение {_q(q['Везение'])}  "
        f"Долг {_q(q['Чувство долга'])}  Память {_q(q['Ум, память'])}  "
        f"Темперамент {_q(q['Темперамент'])}",
        f"  Самооценка {_q(q['Самооценка'])}  Целеустремл. {_q(q['Целеустремлённость'])}  "
        f"Семьянин {_q(q['Качество семьянина'])}  Стабильность {_q(q['Стабильность'])}",
        f"  Число души {sc['Число души']}, ЧЖП {sc['Число жизненного пути (ЧЖП)']}, "
        f"уровень сознания {sc['Уровень сознания']}, код поведения «{sc['Код поведения']}»",
        "Дни (вперёд):",
        f"  благоприятные: {', '.join(days['favorable'])}",
        f"  критические:   {', '.join(days['critical']) or '—'}",
        f"  травмоопасные: {', '.join(days['traumatic'])}",
        "Прогноз на 5 лет (год/возраст: персон.число · Луна/Солнце · год±/энергия · судьба):",
    ]
    for f in rep["forecast"]:
        cyc = f" · 12-цикл {f['rebirth_cycle']}" if f["fate"] == "+" else ""
        lines.append(
            f"  {f['year']}/{f['age']}: ПЧ{f['personal_year']} ({f['personal_year_text']}) · "
            f"Л{f['moon']}/С{f['sun']} · {f['year_value']:+d} «{f['year_value_text']}» · "
            f"E{f['energy_potential']} · {f['fate']}{cyc}"
        )
    lines.append(
        f"Личные числа: ЧПГ {pn['personal_year']}, ЧПМ {pn['personal_month']}, "
        f"ЧПД {pn['personal_day']}  (комбо {pn['combo_key']})"
    )
    mv = ", ".join(f"{m['month_name'][:3]}{m['value']:+d}" for m in ms["monthly"])
    lines.append(f"Луна/Солнце по месяцам (код): {mv}")
    return "\n".join(lines)


def main() -> None:
    for gender, person in DEMO:
        print(render(gender, person))
    print("═" * 70)


if __name__ == "__main__":
    main()
