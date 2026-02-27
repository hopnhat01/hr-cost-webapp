import io
from datetime import date, datetime

import pandas as pd
import streamlit as st
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

from hr_cost.engine import CalculationEngine
from hr_cost.models import Inputs, Holiday, EmployerInsurance


# ----------------------------
# Helpers
# ----------------------------
def to_date(x) -> date | None:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return None
    if isinstance(x, date) and not isinstance(x, datetime):
        return x
    if isinstance(x, datetime):
        return x.date()
    return pd.to_datetime(x, dayfirst=True).date()


def read_holidays_upload(upload) -> pd.DataFrame:
    """
    Accept CSV/XLSX.
    Expect a date-like column.
    Prefer column name: date / Ngày / ngay / holiday_date.
    """
    if upload is None:
        return pd.DataFrame(columns=["date", "name"])

    fname = upload.name.lower()
    if fname.endswith(".csv"):
        df = pd.read_csv(upload)
    elif fname.endswith(".xlsx") or fname.endswith(".xls"):
        df = pd.read_excel(upload)
    else:
        raise ValueError("Chỉ hỗ trợ CSV hoặc XLSX.")

    # pick date column
    candidates = [c for c in df.columns if str(c).strip().lower() in ["date", "ngày", "ngay", "holiday_date", "ngày nghỉ"]]
    date_col = candidates[0] if candidates else df.columns[0]

    df = df.copy()
    df["date"] = df[date_col].apply(to_date)

    # name column
    if "name" not in df.columns:
        name_candidates = [c for c in df.columns if str(c).strip().lower() in ["name", "tên", "ten", "holiday_name", "tên ngày lễ"]]
        df["name"] = df[name_candidates[0]].astype(str) if name_candidates else ""

    df = df.dropna(subset=["date"]).sort_values("date")
    return df[["date", "name"]].reset_index(drop=True)


def df_to_holidays(df: pd.DataFrame) -> list[Holiday]:
    holidays = []
    for _, r in df.iterrows():
        d = to_date(r.get("date"))
        if d:
            holidays.append(Holiday(date=d, name=str(r.get("name", "") or "")))
    return holidays


def result_rows_to_df(rows: list[dict]) -> pd.DataFrame:
    """
    Convert engine rows -> a user-friendly dataframe similar to MONTHLY_COST.
    """
    df = pd.DataFrame(rows)

    # Reorder columns (friendly)
    col_order = [
        "year", "month",
        "month_start", "month_end",
        "calc_start", "calc_end",
        "F", "G", "H",
        "paid_workdays", "paid_holidays", "I",
        "J", "K",
        "L", "M", "N", "O",
        "P", "Q",
    ]
    df = df[[c for c in col_order if c in df.columns] + [c for c in df.columns if c not in col_order]]

    # Rename for display
    df = df.rename(columns={
        "year": "Năm",
        "month": "Tháng",
        "month_start": "Ngày 1 của tháng",
        "month_end": "Ngày cuối tháng",
        "calc_start": "Bắt đầu tính",
        "calc_end": "Kết thúc tính",
        "F": "Ngày làm việc chuẩn (F)",
        "G": "Ngày nghỉ lễ (G)",
        "H": "Ngày công trả lương chuẩn (H)",
        "paid_workdays": "Ngày làm việc thực tế",
        "paid_holidays": "Ngày lễ thực tế",
        "I": "Ngày công trả lương thực tế (I)",
        "J": "Phép năm thực tế (J)",
        "K": "Lương/ngày (K)",
        "L": "Chi phí làm việc (L)",
        "M": "Chi phí nghỉ phép (M)",
        "N": "Chi phí nghỉ lễ (N)",
        "O": "Tổng lương phải trả (O)",
        "P": "BH NSDLĐ (P)",
        "Q": "TỔNG CHI PHÍ CÔNG TY (Q)",
    })
    return df


def export_excel(result_df: pd.DataFrame, holidays_df: pd.DataFrame, inputs_dict: dict) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "RESULT"

    ws.append(["INPUTS"])
    for k, v in inputs_dict.items():
        ws.append([k, v])
    ws.append([])
    ws.append(["MONTHLY_COST"])

    for r in dataframe_to_rows(result_df, index=False, header=True):
        ws.append(r)

    ws2 = wb.create_sheet("HOLIDAYS")
    ws2.append(["date", "name"])
    for _, row in holidays_df.iterrows():
        ws2.append([to_date(row["date"]), row.get("name", "")])

    bio = io.BytesIO()
    wb.save(bio)
    return bio.getvalue()


# ----------------------------
# UI
# ----------------------------
st.set_page_config(page_title="HR Cost (Mon–Sat)", layout="wide")
st.title("HR Cost Webapp (Mon–Sat) — khớp logic Excel")

with st.sidebar:
    st.header("Inputs")

    gross = st.number_input("Gross/tháng (VND)", min_value=0.0, value=20_000_000.0, step=500_000.0)
    start_dt = st.date_input("Ngày bắt đầu", value=date(2026, 4, 15))
    end_dt = st.date_input("Ngày kết thúc", value=date(start_dt.year, 12, 31))
    year = st.number_input("Năm tính (YYYY)", min_value=2000, max_value=2100, value=int(start_dt.year), step=1)
    annual_leave_days = st.number_input("Phép năm (ngày/năm)", min_value=0.0, value=12.0, step=1.0)

    st.divider()
    st.subheader("BH NSDLĐ")
    ins_enabled = st.checkbox("Bật tính BH NSDLĐ", value=True)
    ins_rate = st.number_input("Tỷ lệ BH", min_value=0.0, max_value=1.0, value=0.215, step=0.001, format="%.3f")
    ins_cap = st.number_input("Trần BH (0 = không trần)", min_value=0.0, value=5_500_000.0, step=100_000.0)

    st.divider()
    st.subheader("Holidays")
    upload = st.file_uploader("Upload holidays (CSV/XLSX)", type=["csv", "xlsx", "xls"])


if start_dt > end_dt:
    st.error("Ngày bắt đầu đang lớn hơn ngày kết thúc.")
    st.stop()

# Holidays input table
try:
    holidays_df = read_holidays_upload(upload)
except Exception as e:
    st.error(f"Lỗi đọc holidays: {e}")
    holidays_df = pd.DataFrame(columns=["date", "name"])

# If empty -> start with blank rows (user tự thêm)
holidays_df = holidays_df.copy()
if holidays_df.empty:
    holidays_df = pd.DataFrame([{"date": None, "name": ""}], columns=["date", "name"])

st.caption("Bạn có thể chỉnh trực tiếp danh sách ngày lễ (thêm/xoá/sửa).")
edited_holidays = st.data_editor(
    holidays_df,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "date": st.column_config.DateColumn("date", format="DD/MM/YYYY"),
        "name": st.column_config.TextColumn("name"),
    },
)

# Build engine inputs
inputs = Inputs(
    gross_monthly=float(gross),
    start_date=start_dt,
    end_date=end_dt,
    annual_leave_days=float(annual_leave_days),
    employer_insurance=EmployerInsurance(
        enabled=bool(ins_enabled),
        rate=float(ins_rate),
        cap=float(ins_cap),
    ),
)

holidays = df_to_holidays(edited_holidays)

engine = CalculationEngine(inputs, holidays)
rows = engine.calculate_year(int(year))
result_df = result_rows_to_df(rows)

# Display
st.subheader("Kết quả theo tháng")
st.dataframe(result_df, use_container_width=True)

# KPI
total_O = float(pd.to_numeric(result_df["Tổng lương phải trả (O)"]).sum())
total_P = float(pd.to_numeric(result_df["BH NSDLĐ (P)"]).sum())
total_Q = float(pd.to_numeric(result_df["TỔNG CHI PHÍ CÔNG TY (Q)"]).sum())

c1, c2, c3 = st.columns(3)
c1.metric("Tổng lương (O)", f"{total_O:,.0f} VND")
c2.metric("Tổng BH (P)", f"{total_P:,.0f} VND")
c3.metric("Tổng chi phí (Q)", f"{total_Q:,.0f} VND")

# Export
inputs_dict = {
    "gross_monthly": gross,
    "start_date": start_dt.strftime("%d/%m/%Y"),
    "end_date": end_dt.strftime("%d/%m/%Y"),
    "year": int(year),
    "annual_leave_days": annual_leave_days,
    "insurance_enabled": ins_enabled,
    "insurance_rate": ins_rate,
    "insurance_cap": ins_cap,
}
xlsx = export_excel(result_df, edited_holidays, inputs_dict)

st.download_button(
    "Download Excel kết quả",
    data=xlsx,
    file_name=f"hr_cost_{year}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)