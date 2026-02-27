HR Cost Calculation Spec (Match Excel Version)
1. Work Schedule

Workdays: Monday → Saturday

Sunday: not working

Holidays:

If holiday falls on Mon–Sat:

Not counted as standard workday

Still counted as paid holiday

If holiday falls on Sunday:

Ignored

2. Monthly Standard Counts

For each month:

F = Standard workdays
= Mon–Sat days in month
minus holidays (Mon–Sat)

G = Paid holidays
= holidays (Mon–Sat)

H = Standard paid days
= F + G

3. Actual Paid Days (Prorate)

I = actual paid days in month

If employee active in month:

paid_workdays = Mon–Sat in active range minus holidays

paid_holidays = holidays in active range

I = paid_workdays + paid_holidays

Else:

I = 0

4. Leave Accrual

Monthly leave accrual:
annual_leave_days / 12

Prorated by:
ratio = actual_paid_days / standard_workdays

J = leave_days = monthly_accrual * ratio

5. Salary Calculation

K = daily_rate = gross_monthly / standard_paid_days

L = cost_work = (paid_workdays - leave_days) * daily_rate

M = cost_leave = leave_days * daily_rate

N = cost_holiday = paid_holidays * daily_rate

O = total_salary = actual_paid_days * daily_rate

6. Employer Insurance

If enabled:

base = min(O, cap) if cap > 0
P = base * rate

Else:
P = 0

7. IMPORTANT — Match Excel Total

Total company cost =

Q = O + P + M + N

Note:
Even though O already includes leave and holiday,
Excel adds M and N again.
This behavior must be preserved.