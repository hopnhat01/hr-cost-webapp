from datetime import date, timedelta
from typing import List
from .models import Holiday


def daterange(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def is_workday_mon_sat(d: date) -> bool:
    """
    Monday = 0
    Sunday = 6
    """
    return d.weekday() <= 5


def holidays_to_set(holidays: List[Holiday]):
    return {h.date for h in holidays}


def count_workdays_mon_sat(start: date, end: date, holidays: List[Holiday]) -> int:
    """
    Count Mon–Sat excluding holidays (if holiday falls on Mon–Sat).
    """
    holiday_set = holidays_to_set(holidays)
    count = 0

    for d in daterange(start, end):
        if is_workday_mon_sat(d) and d not in holiday_set:
            count += 1

    return count


def count_paid_holidays(start: date, end: date, holidays: List[Holiday]) -> int:
    """
    Count holidays that fall on Mon–Sat.
    """
    holiday_set = holidays_to_set(holidays)
    count = 0

    for d in daterange(start, end):
        if d in holiday_set and is_workday_mon_sat(d):
            count += 1

    return count