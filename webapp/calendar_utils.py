from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable, List, Set


def _easter_sunday(year: int) -> date:
    # Anonymous Gregorian algorithm
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def brazil_national_holidays(year: int) -> Set[date]:
    # Feriados nacionais (fixos + móveis principais)
    e = _easter_sunday(year)
    carnival = e - timedelta(days=47)  # terça de carnaval
    good_friday = e - timedelta(days=2)
    corpus_christi = e + timedelta(days=60)

    fixed = {
        date(year, 1, 1),   # Confraternização Universal
        date(year, 4, 21),  # Tiradentes
        date(year, 5, 1),   # Dia do Trabalhador
        date(year, 9, 7),   # Independência do Brasil
        date(year, 10, 12), # Nossa Senhora Aparecida
        date(year, 11, 2),  # Finados
        date(year, 11, 15), # Proclamação da República
        date(year, 12, 25), # Natal
    }
    movable = {carnival, good_friday, corpus_christi}
    return fixed | movable


def generate_teaching_dates(start: date, end: date, weekdays: Iterable[int], exclude: Set[date]) -> List[date]:
    # weekdays as Python weekday(): 0=Mon .. 6=Sun
    wset = set(int(w) for w in weekdays)
    out: List[date] = []
    cur = start
    while cur <= end:
        if cur.weekday() in wset and cur not in exclude:
            out.append(cur)
        cur += timedelta(days=1)
    return out

