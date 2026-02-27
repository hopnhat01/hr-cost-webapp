import calendar as pycal
from datetime import date
from typing import List, Dict

from .models import Inputs, Holiday
from .calendar import count_workdays_mon_sat, count_paid_holidays


class CalculationEngine:
    """
    Engine chịu trách nhiệm tính toán toàn bộ logic theo spec.md
    Không phụ thuộc Streamlit/UI.
    """

    def __init__(self, inputs: Inputs, holidays: List[Holiday]):
        self.inputs = inputs
        self.holidays = holidays

    @staticmethod
    def _month_start_end(year: int, month: int) -> tuple[date, date]:
        month_start = date(year, month, 1)
        month_end = date(year, month, pycal.monthrange(year, month)[1])
        return month_start, month_end

    def _calculate_standard_month_counts(self, year: int, month: int) -> Dict[str, int]:
        """
        Spec:
            F = standard_workdays (Mon–Sat) excluding holidays (Mon–Sat)
            G = paid_holidays (holidays that fall on Mon–Sat)
            H = F + G
        """
        ms, me = self._month_start_end(year, month)

        F = count_workdays_mon_sat(ms, me, self.holidays)
        G = count_paid_holidays(ms, me, self.holidays)
        H = F + G

        return {"F": F, "G": G, "H": H}

    def calculate_year(self):
        """
        Placeholder cho bước sau.
        """
        raise NotImplementedError("Chưa implement calculate_year()")