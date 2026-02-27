from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class EmployerInsurance:
    enabled: bool = True
    rate: float = 0.215          # 21.5%
    cap: float = 5_500_000       # 0 = no cap


@dataclass
class Inputs:
    gross_monthly: float
    start_date: date
    end_date: date
    annual_leave_days: float = 12.0
    employer_insurance: EmployerInsurance = EmployerInsurance()


@dataclass
class Holiday:
    date: date
    name: str = ""