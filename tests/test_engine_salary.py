from datetime import date

from hr_cost.engine import CalculationEngine
from hr_cost.models import Inputs


def test_daily_rate_and_total_salary_full_month():
    inputs = Inputs(
        gross_monthly=12_000_000,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
    )

    engine = CalculationEngine(inputs, [])

    std = engine._calculate_standard_month_counts(2026, 1)
    actual = engine._calculate_actual_paid_days(2026, 1)

    res = engine._calculate_salary(2026, 1)

    assert res["daily_rate"] > 0
    assert res["O"] == actual["I"] * res["daily_rate"]


def test_salary_zero_when_not_active():
    inputs = Inputs(
        gross_monthly=12_000_000,
        start_date=date(2026, 2, 1),
        end_date=date(2026, 2, 28),
    )

    engine = CalculationEngine(inputs, [])

    res = engine._calculate_salary(2026, 1)

    assert res["O"] == 0