from datetime import date

from hr_cost.engine import CalculationEngine
from hr_cost.models import Inputs, Holiday


def test_standard_counts_no_holiday():
    inputs = Inputs(
        gross_monthly=20_000_000,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
    )

    holidays = []

    engine = CalculationEngine(inputs, holidays)

    result = engine._calculate_standard_month_counts(2026, 1)

    assert result["F"] > 0
    assert result["G"] == 0
    assert result["H"] == result["F"]


def test_standard_counts_with_holiday():
    inputs = Inputs(
        gross_monthly=20_000_000,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
    )

    holidays = [
        Holiday(date=date(2026, 1, 5), name="Test Monday")
    ]

    engine = CalculationEngine(inputs, holidays)

    result = engine._calculate_standard_month_counts(2026, 1)

    assert result["G"] == 1
    assert result["H"] == result["F"] + result["G"]