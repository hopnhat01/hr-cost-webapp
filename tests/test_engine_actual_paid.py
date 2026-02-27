from datetime import date

from hr_cost.engine import CalculationEngine
from hr_cost.models import Inputs, Holiday


def test_actual_paid_days_outside_month_is_zero():
    # employee active only in Feb, test Jan
    inputs = Inputs(
        gross_monthly=20_000_000,
        start_date=date(2026, 2, 1),
        end_date=date(2026, 2, 28),
    )
    engine = CalculationEngine(inputs, [])

    res = engine._calculate_actual_paid_days(2026, 1)
    assert res["I"] == 0
    assert res["paid_workdays"] == 0
    assert res["paid_holidays"] == 0


def test_actual_paid_days_mid_month_prorate():
    # Active 15/04/2026 -> 30/04/2026
    inputs = Inputs(
        gross_monthly=20_000_000,
        start_date=date(2026, 4, 15),
        end_date=date(2026, 4, 30),
    )
    engine = CalculationEngine(inputs, [])

    res = engine._calculate_actual_paid_days(2026, 4)

    # sanity checks
    assert res["I"] > 0
    assert res["paid_holidays"] == 0
    assert res["I"] == res["paid_workdays"]


def test_actual_paid_days_counts_holiday_in_active_range():
    # Active whole Jan, one holiday on Mon
    inputs = Inputs(
        gross_monthly=20_000_000,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
    )
    holidays = [Holiday(date=date(2026, 1, 5), name="Test Monday")]
    engine = CalculationEngine(inputs, holidays)

    res = engine._calculate_actual_paid_days(2026, 1)

    assert res["paid_holidays"] == 1
    assert res["I"] == res["paid_workdays"] + 1