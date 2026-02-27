from datetime import date

from hr_cost.calendar import (
    count_workdays_mon_sat,
    count_paid_holidays,
)
from hr_cost.models import Holiday


def test_basic_month_no_holidays():
    """
    Tháng 1/2026 không có holiday.
    Kiểm tra:
    - Có workdays > 0
    - Không có paid holiday
    """
    holidays = []

    start = date(2026, 1, 1)
    end = date(2026, 1, 31)

    workdays = count_workdays_mon_sat(start, end, holidays)
    holidays_count = count_paid_holidays(start, end, holidays)

    assert workdays > 0
    assert holidays_count == 0


def test_holiday_on_sunday_not_counted():
    """
    Holiday rơi vào Chủ nhật:
    - Không tính là paid holiday
    - Không ảnh hưởng workday chuẩn
    """

    # 4/1/2026 là Chủ nhật
    holidays = [
        Holiday(date=date(2026, 1, 4), name="Test Sunday")
    ]

    start = date(2026, 1, 1)
    end = date(2026, 1, 31)

    holidays_count = count_paid_holidays(start, end, holidays)

    assert holidays_count == 0


def test_holiday_on_weekday_counted():
    """
    Holiday rơi vào ngày làm việc (T2–T7):
    - Được tính là paid holiday
    """

    # 5/1/2026 là Thứ Hai
    holidays = [
        Holiday(date=date(2026, 1, 5), name="Test Monday")
    ]

    start = date(2026, 1, 1)
    end = date(2026, 1, 31)

    holidays_count = count_paid_holidays(start, end, holidays)

    assert holidays_count == 1