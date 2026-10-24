
from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace

from app.services.forecasting import calculate_forecast


# ==========================================
# HELPER: CREATE SAMPLE USAGE RECORDS
# ==========================================

def make_records(quantities):

    start_date = date(2026, 10, 16)

    records = []

    for index, quantity in enumerate(quantities):

        record = SimpleNamespace(
            usage_date=start_date + timedelta(days=index),
            quantity_used=Decimal(quantity)
        )

        records.append(record)

    return records


# ==========================================
# TEST 1: NORMAL FORECAST
# ==========================================

def test_forecast_normal_usage():

    records = make_records([
        "0.40",
        "0.35",
        "0.45",
        "0.50",
        "0.30",
        "0.40",
        "0.40"
    ])

    result = calculate_forecast(
        records,
        Decimal("20.00")
    )

    assert result is not None

    assert result["average_daily_usage"] == Decimal("0.40")

    assert result["forecast_30_days"] == Decimal("12.00")

    assert result["forecast_60_days"] == Decimal("24.00")

    assert result["forecast_90_days"] == Decimal("36.00")

    assert result["days_remaining"] == Decimal("50.00")


# ==========================================
# TEST 2: INSUFFICIENT DATA
# ==========================================

def test_forecast_insufficient_data():

    records = make_records([
        "0.40",
        "0.35",
        "0.45",
        "0.50",
        "0.30",
        "0.40"
    ])

    result = calculate_forecast(
        records,
        Decimal("20.00")
    )

    assert result is None


# ==========================================
# TEST 3: NON-CONSECUTIVE DATES
# ==========================================

def test_forecast_missing_day():

    records = make_records([
        "0.40",
        "0.35",
        "0.45",
        "0.50",
        "0.30",
        "0.40",
        "0.40"
    ])

    # Move the last date forward by one day.
    # This creates a gap in the usage history.
    records[-1].usage_date += timedelta(days=1)

    result = calculate_forecast(
        records,
        Decimal("20.00")
    )

    assert result is None


# ==========================================
# TEST 4: ZERO DAILY CONSUMPTION
# ==========================================

def test_forecast_zero_usage():

    records = make_records([
        "0.00",
        "0.00",
        "0.00",
        "0.00",
        "0.00",
        "0.00",
        "0.00"
    ])

    result = calculate_forecast(
        records,
        Decimal("20.00")
    )

    assert result is not None

    assert result["average_daily_usage"] == Decimal("0.00")

    assert result["forecast_30_days"] == Decimal("0.00")

    # No consumption means stock coverage cannot
    # be estimated by dividing stock by daily usage.
    assert result["days_remaining"] is None


# ==========================================
# TEST 5: UNSORTED HISTORICAL DATA
# ==========================================

def test_forecast_unsorted_records():

    records = make_records([
        "5.00",
        "5.00",
        "0.50",
        "0.50",
        "0.50",
        "0.50",
        "0.50",
        "0.50",
        "0.50"
    ])

    # Reverse chronological order intentionally
    records.reverse()

    result = calculate_forecast(
        records,
        Decimal("20.00")
    )

    assert result is not None

    # Only the latest seven consecutive days
    # should be used in the calculation.
    assert result["average_daily_usage"] == Decimal("0.50")

    assert result["forecast_30_days"] == Decimal("15.00")
