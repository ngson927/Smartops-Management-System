
from datetime import timedelta
from decimal import Decimal


def calculate_forecast(usage_records, current_stock):
    # 1. Sort usage records by date
    records = sorted(
        usage_records,
        key=lambda record: record.usage_date
    )

    # 2. Get the latest 7 days
    last_7_days = records[-7:]

    if len(last_7_days) < 7:
        return None

    # 3. Ensure the records cover 7 consecutive days
    for i in range(1, 7):
        expected_date = (
            last_7_days[i - 1].usage_date
            + timedelta(days=1)
        )

        if last_7_days[i].usage_date != expected_date:
            return None

    # 4. Calculate total and average daily usage
    total_usage = sum(
        (record.quantity_used for record in last_7_days),
        Decimal("0.00")
    )

    average_daily_usage = total_usage / Decimal("7")

    # 5. Forecast future demand
    forecast_30 = average_daily_usage * 30
    forecast_60 = average_daily_usage * 60
    forecast_90 = average_daily_usage * 90

    # 6. Estimate days until stock runs out
    if average_daily_usage > 0:
        days_remaining = (
            Decimal(current_stock) / average_daily_usage
        )
    else:
        days_remaining = None

    # 7. Return forecasting results
    return {
        "as_of_date": last_7_days[-1].usage_date.isoformat(),
        "average_daily_usage": average_daily_usage.quantize(
            Decimal("0.01")
        ),
        "forecast_30_days": forecast_30.quantize(
            Decimal("0.01")
        ),
        "forecast_60_days": forecast_60.quantize(
            Decimal("0.01")
        ),
        "forecast_90_days": forecast_90.quantize(
            Decimal("0.01")
        ),
        "days_remaining": (
            days_remaining.quantize(Decimal("0.01"))
            if days_remaining is not None
            else None
        )
    }
