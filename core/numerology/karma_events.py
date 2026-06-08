"""Кармические события (лист РАСЧЕТ BG17/BG20 ← лист Matr строки 4–5).

Источник истины: лист Excel «Matr»/«РАСЧЕТ». Сверено с кэшем книги (субъект
20.02.1990, мать 06.08.1971, отец 23.11.1970), нулевой допуск:
- BG17 → «событие негативного характера в возрасте 28»;
- BG20 → «подъём в возрасте 28».

Оба события зависят от дат рождения РОДИТЕЛЕЙ (опц. поля анкеты):
- 1-е событие (строка 4) ← дата МАТЕРИ  (Matr Q4:X4 = MID-цифры DAY/MONTH/YEAR(P4));
- 2-е событие (строка 5) ← дата ОТЦА    (Matr Q5:X5 = цифры P5).
Без даты соответствующего родителя книга даёт #VALUE! (как в пустом примере
01.01.2000) → здесь событие просто не формируется (None), строка в отчёт не идёт.

Цепочка (см. docs/excel-analysis.md M.14, R.2):
BD7 = Σ8 цифр даты субъекта; BE7 = свод(BD7).
Строка 4 (мать):  Y4=Σцифр(P4); Z4=md2(Y4); AA4=md2(Z4); AB4=md2(AA4);
  AC4=BE7; AD4=md2(AC4); AE4=⌊(AB4+AD4)/2⌋; AF4="+" если AE4 чётное иначе "−";
  AG4=BD7+AE4.  BG17 = «событие {+полож./−негат.} характера в возрасте AG4».
Строка 5 (отец):  Y5=Σцифр(P5); AC5=BD7; Z5=(Y5+AC5)/2 (General-строка Excel);
  AD5=Z5[0], AE5=Z5[1]; AF5="+" если AE5>AD5 (сравнение строк) иначе "−";
  AA5=md2(Z5); AB5=md2(AA5); AG5=AC5+AB5.
  BG20 = «{+подъём/−спуск} в возрасте AG5».
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from core.numerology._digits import date_digits, digit_sum
from core.numerology.person import PersonInput


def _md2(s: str) -> int:
    """Excel MID(s,1,1)+IF(MID(s,2,1)="",0,MID(s,2,1)): 1-я цифра + 2-я (или 0).

    Не-цифра во 2-й позиции (точка дробного Z) трактуется как 0 — в книге это
    место даёт #VALUE!, здесь считаем мягко, чтобы не падать на малых суммах.
    """
    a = int(s[0])
    b = int(s[1]) if len(s) > 1 and s[1].isdigit() else 0
    return a + b


def _excel_half(total: int) -> str:
    """(total)/2 в General-формате Excel: чёт → «23», нечёт → «23.5»."""
    return str(total // 2) if total % 2 == 0 else f"{total // 2}.5"


@dataclass(frozen=True)
class KarmaEvent:
    sign: str  # "+" / "-" (AF4 / AF5)
    age: int  # возраст события (AG4 / AG5)
    text: str  # готовая строка отчёта (BG17 / BG20)

    def as_dict(self) -> dict:
        return asdict(self)


def compute_karma_events(person: PersonInput) -> dict:
    """Два кармических события (BG17/BG20). Требуют даты матери/отца соответственно.

    Возвращает {"first": {...}|None, "second": {...}|None}: None, если у субъекта
    не указана дата рождения соответствующего родителя.
    """
    bd7 = sum(date_digits(person.birth_date))  # духовный уровень
    be7 = digit_sum(bd7)

    first = None
    if person.mother_birth_date is not None:
        y4 = sum(date_digits(person.mother_birth_date))
        ab4 = _md2(str(_md2(str(_md2(str(y4))))))  # AB4 ← AA4 ← Z4 ← Y4
        ad4 = _md2(str(be7))  # AC4 = BE7
        ae4 = (ab4 + ad4) // 2  # ROUNDDOWN(/2, 0)
        af4 = "+" if ae4 % 2 == 0 else "-"
        ag4 = bd7 + ae4
        label = (
            "событие положительного характера " if af4 == "+" else "событие негативного характера "
        )
        first = KarmaEvent(af4, ag4, f"{label}в возрасте {ag4}").as_dict()

    second = None
    if person.father_birth_date is not None:
        y5 = sum(date_digits(person.father_birth_date))
        ac5 = bd7
        z5 = _excel_half(y5 + ac5)
        ad5, ae5 = z5[0], (z5[1] if len(z5) > 1 else "")
        af5 = "+" if ae5 > ad5 else "-"
        ab5 = _md2(str(_md2(z5)))  # AB5 ← AA5 ← Z5
        ag5 = ac5 + ab5
        label = "подъём " if af5 == "+" else "спуск "
        second = KarmaEvent(af5, ag5, f"{label}в возрасте {ag5}").as_dict()

    return {"first": first, "second": second}
