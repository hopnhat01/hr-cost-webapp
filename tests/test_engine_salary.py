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
    sal = engine._calculate_salary_breakdown(2026, 1)

    # K > 0
    assert sal["K"] > 0

    # O = I * K
    assert sal["O"] == actual["I"] * sal["K"]

    # K = gross / H
    assert sal["K"] == inputs.gross_monthly / std["H"]


def test_salary_zero_when_not_active():
    inputs = Inputs(
        gross_monthly=12_000_000,
        start_date=date(2026, 2, 1),
        end_date=date(2026, 2, 28),
    )

    engine = CalculationEngine(inputs, [])

    sal = engine._calculate_salary_breakdown(2026, 1)

    assert sal["O"] == 0
    assert sal["L"] == 0
    assert sal["M"] == 0
    assert sal["N"] == 0