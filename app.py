import io
import calendar
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st
from dateutil.relativedelta import relativedelta
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

def check_password():
    if "password_correct" not in st.session_state:
        st.text_input("Nhap mat khau de xam nhap he thong", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Sai mat khau, yeu cau nhap lai", type="password", on_change=password_entered, key="password")
        return False
    else:
        return True

def password_entered():
    if st.session_state["password"] == "123456":
        st.session_state["password_correct"] = True
        del st.session_state["password"]
    else:
        st.session_state["password_correct"] = False

if not check_password():
    st.stop()

def to_date(x) -> date:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return None
    if isinstance(x, date) and not isinstance(x, datetime):
        return x
    if isinstance(x, datetime):
        return x.date()
    return pd.to_datetime(x, dayfirst=True).date()

def is_workday_mon_sat(d: date) -> bool:
    return d.weekday() <= 5

def daterange(d1: date, d2: date):
    cur = d1
    while cur <= d2:
        yield cur
        cur += timedelta(days=1)

def count_workdays_mon_sat(start: date, end: date, holidays_set: set[date]) -> int:
    cnt = 0
    for d in daterange(start, end):
        if is_workday_mon_sat(d) and (d not in holidays_set):
            cnt += 1
    return cnt

def count_holidays_monsat(start: date, end: date, holidays_set: set[date]) -> int:
    cnt = 0
    for d in daterange(start, end):
        if d in holidays_set and is_workday_mon_sat(d):
            cnt += 1
    return cnt

def month_start_end(year: int, month: int) -> tuple[date, date]:
    ms = date(year, month, 1)
    me = date(year, month, calendar.monthrange(year, month)[1])
    return ms, me

def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

def parse_holidays_upload(upload) -> pd.DataFrame:
    if upload is None:
        return pd.DataFrame(columns=["date", "name"])

    name = upload.name.lower()
    if name.endswith(".csv"):
        df = pd.read_csv(upload)
    elif name.endswith(".xlsx") or name.endswith(".xls"):
        df = pd.read_excel(upload)
    else:
        raise ValueError("Chi ho tro CSV hoac XLSX.")

    candidates = [c for c in df.columns if str(c).strip().lower() in ["date", "ngày", "ngay", "holiday_date", "ngày nghỉ", "ngày nghỉ (dd/mm/yyyy)"]]
    if candidates:
        date_col = candidates[0]
    else:
        date_col = df.columns[0]

    df = df.copy()
    df["date"] = df[date_col].apply(to_date)
    
    name_candidates = [c for c in df.columns if str(c).strip().lower() in ["name", "tên", "ten", "holiday_name", "tên ngày lễ"]]
    if name_candidates:
        df["name"] = df[name_candidates[0]].astype(str)
    else:
        df["name"] = ""
        
    df = df.dropna(subset=["date"]).sort_values("date")
    df = df[["date", "name"]].reset_index(drop=True)
    return df

def default_holidays_for_year(year: int) -> pd.DataFrame:
    samples = [
        (date(year, 1, 1), "Tet Duong lich"),
        (date(year, 4, 30), "Ngay Chien thang"),
        (date(year, 5, 1), "Quoc te Lao dong"),
        (date(year, 9, 2), "Quoc khanh"),
    ]
    return pd.DataFrame(samples, columns=["date", "name"])

def calculate_monthly_cost(
    year: int,
    gross: float,
    start_date: date,
    end_date: date,
    annual_leave_days: float,
    holidays_df: pd.DataFrame,
    employer_ins_enabled: bool,
    employer_ins_rate: float,
    employer_ins_cap: float,
) -> pd.DataFrame:
    holidays_set = set(holidays_df["date"].dropna().tolist())
    monthly_leave_accrual = annual_leave_days / 12.0
    rows = []

    for m in range(1, 13):
        ms, me = month_start_end(year, m)
        calc_start = max(start_date, ms)
        calc_end = min(end_date, me)

        standard_workdays = count_workdays_mon_sat(ms, me, holidays_set)  
        month_holidays = count_holidays_monsat(ms, me, holidays_set)      
        standard_paid_days = standard_workdays + month_holidays           

        if calc_start > calc_end:
            actual_paid_days = 0
            paid_workdays = 0
            paid_holidays = 0
        else:
            paid_workdays = count_workdays_mon_sat(calc_start, calc_end, holidays_set)
            paid_holidays = count_holidays_monsat(calc_start, calc_end, holidays_set)
            actual_paid_days = paid_workdays + paid_holidays              

        if standard_workdays <= 0:
            ratio = 0.0
        else:
            ratio = clamp(actual_paid_days / float(standard_workdays), 0.0, 1.0)
        leave_days = monthly_leave_accrual * ratio

        daily_rate = (gross / standard_paid_days) if standard_paid_days > 0 else 0.0

        cost_work = max(0.0, paid_workdays - leave_days) * daily_rate     
        cost_leave = min(leave_days, float(paid_workdays)) * daily_rate   
        cost_holiday = float(paid_holidays) * daily_rate                  
        salary_total = float(actual_paid_days) * daily_rate               

        if employer_ins_enabled:
            base = salary_total
            if employer_ins_cap and employer_ins_cap > 0:
                base = min(base, employer_ins_cap)
            employer_ins = base * employer_ins_rate
        else:
            employer_ins = 0.0

        total_company_cost = salary_total + cost_leave + cost_holiday + employer_ins

        rows.append({
            "Thang": f"{m:02d}",
            "Ngay 1 cua thang": ms,
            "Ngay cuoi thang": me,
            "Bat dau tinh": calc_start,
            "Ket thuc tinh": calc_end,
            "Ngay lam viec chuan": standard_workdays,
            "Ngay nghi le": month_holidays,
            "Ngay cong chuan": standard_paid_days,
            "Ngay cong thuc te": actual_paid_days,
            "Phep nam thuc te": leave_days, 
            "Luong/ngay": daily_rate,
            "Chi phi lam viec": cost_work,
            "Chi phi nghi phep": cost_leave,
            "Chi phi nghi le": cost_holiday,
            "Tong luong phai tra": salary_total,
            "BH NSDLĐ": employer_ins,
            "TONG CHI PHI CÔNG TY": total_company_cost,
        })

    return pd.DataFrame(rows)

def export_to_excel(result_df: pd.DataFrame, holidays_df: pd.DataFrame, inputs: dict) -> bytes:
    wb = Workbook()
    ws1 = wb.active
    ws1.title = "RESULT"

    ws1.append(["INPUTS"])
    for k, v in inputs.items():
        ws1.append([k, v])
    ws1.append([])
    ws1.append(["MONTHLY_COST"])

    for r in dataframe_to_rows(result_df, index=False, header=True):
        ws1.append(r)

    ws2 = wb.create_sheet("HOLIDAYS")
    ws2.append(["date", "name"])
    for _, row in holidays_df.iterrows():
        ws2.append([row["date"], row.get("name", "")])

    bio = io.BytesIO()
    wb.save(bio)
    return bio.getvalue()

st.set_page_config(page_title="Mo hinh nhan su", layout="wide")
st.title("Mo hinh chi phi nhan su theo thang")

with st.sidebar:
    st.header("Thong tin dau vao")
    gross = st.number_input("Luong gross / thang", min_value=0.0, value=20_000_000.0, step=500_000.0)
    start_dt = st.date_input("Ngay bat dau", value=date(2026, 4, 15))
    default_end = date(start_dt.year, 12, 31)
    end_dt = st.date_input("Ngay ket thuc", value=default_end)
    year = st.number_input("Nam can tinh", min_value=2000, max_value=2100, value=int(start_dt.year), step=1)
    annual_leave_days = st.number_input("So ngay phep nam", min_value=0.0, value=12.0, step=1.0)

    st.divider()
    employer_ins_enabled = st.checkbox("Tinh Bao Hiem", value=True)
    employer_ins_rate = st.number_input("Ty le Bao Hiem", min_value=0.0, max_value=1.0, value=0.215, step=0.001, format="%.3f")
    employer_ins_cap = st.number_input("Tran luong dong BH", min_value=0.0, value=5_500_000.0, step=100_000.0)

    st.divider()
    st.subheader("Ngay Le")
    upload = st.file_uploader("Tai tep ngay le len", type=["csv", "xlsx", "xls"])
    use_default = st.checkbox("Dung danh sach mau", value=True)

try:
    holidays_df = parse_holidays_upload(upload)
except Exception as e:
    st.error(f"Loi: {e}")
    holidays_df = pd.DataFrame(columns=["date", "name"])

if holidays_df.empty and use_default:
    holidays_df = default_holidays_for_year(int(year))

holidays_df = holidays_df.copy()
holidays_df["date"] = holidays_df["date"].apply(to_date)
holidays_df = holidays_df.dropna(subset=["date"])
holidays_df = holidays_df[holidays_df["date"].apply(lambda d: d.year == int(year))].reset_index(drop=True)

colA, colB = st.columns([2, 1])
with colA:
    edited_holidays = st.data_editor(
        holidays_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "date": st.column_config.DateColumn("date", format="DD/MM/YYYY"),
            "name": st.column_config.TextColumn("name"),
        }
    )

if start_dt > end_dt:
    st.error("Ngay bat dau lon hon ngay ket thuc.")
    st.stop()

result_df = calculate_monthly_cost(
    year=int(year),
    gross=float(gross),
    start_date=start_dt,
    end_date=end_dt,
    annual_leave_days=float(annual_leave_days),
    holidays_df=edited_holidays,
    employer_ins_enabled=bool(employer_ins_enabled),
    employer_ins_rate=float(employer_ins_rate),
    employer_ins_cap=float(employer_ins_cap),
)

st.subheader("Bang Ket Qua Chi Phi")
st.dataframe(result_df, use_container_width=True)

total_salary = float(result_df["Tong luong phai tra"].sum())
total_ins = float(result_df["BH NSDLĐ"].sum())
total_company = float(result_df["TONG CHI PHI CÔNG TY"].sum())

k1, k2, k3 = st.columns(3)
k1.metric("Tong luong phai tra", f"{total_salary:,.0f} VND")
k2.metric("Tong Bao Hiem", f"{total_ins:,.0f} VND")
k3.metric("Tong chi phi cong ty", f"{total_company:,.0f} VND")

inputs = {
    "gross": gross,
    "start_date": start_dt.strftime("%d/%m/%Y"),
    "end_date": end_dt.strftime("%d/%m/%Y"),
    "year": int(year),
    "annual_leave_days": annual_leave_days,
    "employer_ins_enabled": employer_ins_enabled,
    "employer_ins_rate": employer_ins_rate,
    "employer_ins_cap": employer_ins_cap,
}
xlsx_bytes = export_to_excel(result_df, edited_holidays, inputs)

st.download_button(
    "Tai xuong bang Excel",
    data=xlsx_bytes,
    file_name=f"Chi_phi_nhan_su_{year}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
