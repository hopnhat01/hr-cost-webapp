from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class EmployerInsurance:
    enabled: bool = True
    rate: float = 0.215          # 21.5%
    cap: float = 5_500_000       # 0 = no cap


@dataclass(frozen=True)
class Inputs:
    gross_monthly: float
    start_date: date
    end_date: date
    annual_leave_days: float = 12.0
    employer_insurance: EmployerInsurance = field(default_factory=EmployerInsurance)


@dataclass(frozen=True)
class Holiday:
    date: date
    name: str = ""