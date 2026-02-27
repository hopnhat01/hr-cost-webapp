import calendar as pycal
from datetime import date
from typing import Any, Dict, List

from .calendar import count_paid_holidays, count_workdays_mon_sat
from .models import Holiday, Inputs


class CalculationEngine:
    """
    Calculation Engine (match spec.md / Excel behavior)
    - No UI dependencies
    - Pure business logic

    Naming (match spec.md):
      F = standard_workdays (Mon–Sat excluding holidays on Mon–Sat)
      G = paid_holidays (holidays on Mon–Sat)
      H = standard_paid_days = F + G

      paid_workdays = Mon–Sat in active range excluding holidays
      paid_holidays = holidays (Mon–Sat) in active range
      I = actual_paid_days = paid_workdays + paid_holidays

      J = leave_days (monthly accrual prorated by I/F)
      K = daily_rate = gross_monthly / H

      L = cost_work
      M = cost_leave
      N = cost_holiday
      O = total_salary = I * K

      P = employer insurance
      Q = total_company_cost (IMPORTANT: Excel behavior) = O + P + M + N
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

    @staticmethod
    def _clamp(x: float, lo: float, hi: float) -> float:
        return max(lo, min(hi, x))

    # ----------------------------
    # Spec section 2: Standard month counts (F,G,H)
    # ----------------------------
    def _calculate_standard_month_counts(self, year: int, month: int) -> Dict[str, int]:
        ms, me = self._month_start_end(year, month)

        F = count_workdays_mon_sat(ms, me, self.holidays)
        G = count_paid_holidays(ms, me, self.holidays)
        H = F + G

        return {"F": F, "G": G, "H": H}

    # ----------------------------
    # Spec section 3: Actual paid days (I) within active range
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
    # Spec section 4: Leave accrual (J)
    # monthly_accrual = annual_leave_days / 12
    # ratio = I / F (clamped 0..1), if F==0 => ratio=0
    # J = monthly_accrual * ratio
    # ----------------------------
    def _calculate_leave_days(self, year: int, month: int) -> Dict[str, Any]:
        std = self._calculate_standard_month_counts(year, month)
        actual = self._calculate_actual_paid_days(year, month)

        F = std["F"]
        I = actual["I"]

        monthly_accrual = float(self.inputs.annual_leave_days) / 12.0

        if F <= 0:
            ratio = 0.0
        else:
            ratio = self._clamp(I / float(F), 0.0, 1.0)

        J = monthly_accrual * ratio

        # Guard: do not let leave exceed paid_workdays (prevents negative L in edge cases)
        paid_workdays = actual["paid_workdays"]
        J_capped = min(J, float(paid_workdays))

        return {
            "monthly_accrual": monthly_accrual,
            "ratio": ratio,
            "J": J_capped,
        }

    # ----------------------------
    # Spec section 5: Salary rate (K) and breakdown (L,M,N,O)
    # K = gross_monthly / H (if H==0 => 0)
    # O = I * K
    # N = paid_holidays * K
    # M = J * K
    # L = (paid_workdays - J) * K
    # ----------------------------
    def _calculate_salary_breakdown(self, year: int, month: int) -> Dict[str, Any]:
        std = self._calculate_standard_month_counts(year, month)
        actual = self._calculate_actual_paid_days(year, month)
        leave = self._calculate_leave_days(year, month)

        H = std["H"]
        I = actual["I"]
        paid_workdays = actual["paid_workdays"]
        paid_holidays = actual["paid_holidays"]
        J = leave["J"]

        K = (float(self.inputs.gross_monthly) / float(H)) if H > 0 else 0.0

        L = (float(paid_workdays) - float(J)) * K
        M = float(J) * K
        N = float(paid_holidays) * K
        O = float(I) * K

        return {
            "K": K,
            "L": L,
            "M": M,
            "N": N,
            "O": O,
            "H": H,
            "I": I,
            "paid_workdays": paid_workdays,
            "paid_holidays": paid_holidays,
            "J": J,
        }

    # ----------------------------
    # Spec section 6: Employer insurance (P)
    # base = min(O, cap) if cap>0 else O
    # P = base * rate if enabled else 0
    # ----------------------------
    def _calculate_employer_insurance(self, O: float) -> float:
        ins = self.inputs.employer_insurance
        if not ins.enabled:
            return 0.0

        base = float(O)
        if ins.cap and ins.cap > 0:
            base = min(base, float(ins.cap))

        return base * float(ins.rate)

    # ----------------------------
    # Spec section 7: IMPORTANT Excel total (Q)
    # Q = O + P + M + N   (Excel behavior)
    # ----------------------------
    def _calculate_total_company_cost(self, O: float, P: float, M: float, N: float) -> float:
        return float(O) + float(P) + float(M) + float(N)

    # ----------------------------
    # Public: calculate one month row
    # ----------------------------
    def calculate_month(self, year: int, month: int) -> Dict[str, Any]:
        std = self._calculate_standard_month_counts(year, month)
        actual = self._calculate_actual_paid_days(year, month)
        leave = self._calculate_leave_days(year, month)
        sal = self._calculate_salary_breakdown(year, month)

        ms, me = self._month_start_end(year, month)

        O = sal["O"]
        P = self._calculate_employer_insurance(O)
        Q = self._calculate_total_company_cost(O=O, P=P, M=sal["M"], N=sal["N"])

        return {
            "year": year,
            "month": month,
            "month_start": ms,
            "month_end": me,
            "calc_start": actual["calc_start"],
            "calc_end": actual["calc_end"],
            # Standard counts
            "F": std["F"],
            "G": std["G"],
            "H": std["H"],
            # Actual
            "paid_workdays": actual["paid_workdays"],
            "paid_holidays": actual["paid_holidays"],
            "I": actual["I"],
            # Leave
            "J": leave["J"],
            "leave_ratio": leave["ratio"],
            "leave_monthly_accrual": leave["monthly_accrual"],
            # Salary
            "K": sal["K"],
            "L": sal["L"],
            "M": sal["M"],
            "N": sal["N"],
            "O": sal["O"],
            # Insurance + Total
            "P": P,
            "Q": Q,
        }

    # ----------------------------
    # Public: calculate a full year (12 months)
    # ----------------------------
    def calculate_year(self, year: int) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for m in range(1, 13):
            rows.append(self.calculate_month(year, m))
        return rows