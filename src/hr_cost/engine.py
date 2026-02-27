import calendar as pycal
from datetime import date
from typing import List, Dict, Any

from .models import Inputs, Holiday
from .calendar import count_workdays_mon_sat, count_paid_holidays


class CalculationEngine:
    """
    Calculation Engine (match spec.md)
    - No UI dependencies
    - Pure business logic
    """

    def __init__(self, inputs: Inputs, holidays: List[Holiday]):
        self.inputs = inputs
        self.holidays = holidays

    # ----------------------------
    # Date utilities
    # ----------------------------
    @staticmethod
    def _month_start_end(year: int, month: int) -> tuple[date, date]:
        month_start = date(year, month, 1)
        month_end = date(year, month, pycal.monthrange(year, month)[1])
        return month_start, month_end

    # ----------------------------
    # Spec section 2: Standard counts
    # F = standard_workdays (Mon–Sat excluding holidays on Mon–Sat)
    # G = paid_holidays (holidays on Mon–Sat)
    # H = F + G
    # ----------------------------
    def _calculate_standard_month_counts(self, year: int, month: int) -> Dict[str, int]:
        ms, me = self._month_start_end(year, month)

        F = count_workdays_mon_sat(ms, me, self.holidays)
        G = count_paid_holidays(ms, me, self.holidays)
        H = F + G

        return {"F": F, "G": G, "H": H}

    # ----------------------------
    # Spec section 3: Actual paid days (prorate)
    # calc_start = max(employee start_date, month_start)
    # calc_end   = min(employee end_date, month_end)
    # paid_workdays = Mon–Sat in [calc_start, calc_end] excluding holidays
    # paid_holidays = holidays on Mon–Sat in [calc_start, calc_end]
    # I = paid_workdays + paid_holidays
    # ----------------------------
    def _calculate_actual_paid_days(self, year: int, month: int) -> Dict[str, Any]:
        ms, me = self._month_start_end(year, month)

        calc_start = max(self.inputs.start_date, ms)
        calc_end = min(self.inputs.end_date, me)

        if calc_start > calc_end:
            return {
                "month_start": ms,
                "month_end": me,
                "calc_start": calc_start,
                "calc_end": calc_end,
                "paid_workdays": 0,
                "paid_holidays": 0,
                "I": 0,
            }

        paid_workdays = count_workdays_mon_sat(calc_start, calc_end, self.holidays)
        paid_holidays = count_paid_holidays(calc_start, calc_end, self.holidays)
        I = paid_workdays + paid_holidays

        return {
            "month_start": ms,
            "month_end": me,
            "calc_start": calc_start,
            "calc_end": calc_end,
            "paid_workdays": paid_workdays,
            "paid_holidays": paid_holidays,
            "I": I,
        }

    # ----------------------------
    # Spec section 5 (partial): Salary calculation
    # K = daily_rate = gross_monthly / H
    # O = total_salary = I * K
    # ----------------------------
    def _calculate_salary(self, year: int, month: int) -> Dict[str, Any]:
        std = self._calculate_standard_month_counts(year, month)
        actual = self._calculate_actual_paid_days(year, month)

        H = std["H"]
        I = actual["I"]

        daily_rate = (self.inputs.gross_monthly / H) if H > 0 else 0.0
        O = I * daily_rate

        return {
            "H": H,
            "I": I,
            "daily_rate": daily_rate,
            "O": O,
        }

    # ----------------------------
    # Public API (placeholder)
    # ----------------------------
    def calculate_year(self, year: int):
        """
        Sẽ implement sau (khi có đủ leave, holiday cost, insurance, total).
        Hiện tại mới hỗ trợ tính từng tháng thông qua các method private.
        """
        raise NotImplementedError("Chưa implement calculate_year(year).")