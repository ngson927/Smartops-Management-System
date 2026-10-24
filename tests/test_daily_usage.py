
from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace

from app.services.daily_usage import aggregate_daily_usage


# ==========================================
# HELPER
# ==========================================

def make_transaction(
    transaction_type,
    quantity_change,
    timestamp,
    business_date=None
):

    return SimpleNamespace(
        transaction_type=transaction_type,
        quantity_change=Decimal(quantity_change),
        created_at=timestamp,
        business_date=business_date
    )


# ==========================================
# TEST 1: SAME-DAY CONSUMPTION
# ==========================================

def test_same_day_consumption():

    transactions = [
        make_transaction(
            "OUT",
            "-0.30",
            datetime(2026, 10, 23, 14, 0)
        ),

        make_transaction(
            "OUT",
            "-0.20",
            datetime(2026, 10, 23, 18, 0)
        )
    ]

    result = aggregate_daily_usage(transactions)

    assert len(result) == 1
    assert result[0]["quantity_used"] == "0.50"


# ==========================================
# TEST 2: EXCLUDE OTHER TRANSACTIONS
# ==========================================

def test_exclude_other_transactions():

    transactions = [
        make_transaction(
            "OUT",
            "-0.50",
            datetime(2026, 10, 23, 15, 0)
        ),

        make_transaction(
            "IN",
            "5.00",
            datetime(2026, 10, 23, 16, 0)
        ),

        make_transaction(
            "WASTE",
            "-0.10",
            datetime(2026, 10, 23, 17, 0)
        ),

        make_transaction(
            "ADJUSTMENT",
            "-1.00",
            datetime(2026, 10, 23, 18, 0)
        )
    ]

    result = aggregate_daily_usage(transactions)

    assert len(result) == 1
    assert result[0]["quantity_used"] == "0.50"


# ==========================================
# TEST 3: LOCAL TIMEZONE
# ==========================================

def test_local_date_conversion():

    transactions = [
        make_transaction(
            "OUT",
            "-0.40",
            datetime(2026, 10, 24, 0, 30)
        )
    ]

    result = aggregate_daily_usage(transactions)

    assert result[0]["usage_date"] == "2026-10-23"
    assert result[0]["quantity_used"] == "0.40"


# ==========================================
# TEST 4: BUSINESS DATE PRIORITY
# ==========================================

def test_business_date_takes_priority():

    transaction = make_transaction(
        "OUT",
        "-0.40",
        datetime(2026, 10, 24, 15, 0),
        business_date=date(2026, 10, 22)
    )

    result = aggregate_daily_usage([transaction])

    assert len(result) == 1

    assert result[0]["usage_date"] == "2026-10-22"

    assert result[0]["quantity_used"] == "0.40"


# ==========================================
# TEST 5: GROUP BY BUSINESS DATE
# ==========================================

def test_group_by_business_date():

    transactions = [
        make_transaction(
            "OUT",
            "-0.30",
            datetime(2026, 10, 24, 14, 0),
            business_date=date(2026, 10, 23)
        ),

        make_transaction(
            "OUT",
            "-0.20",
            datetime(2026, 10, 25, 15, 0),
            business_date=date(2026, 10, 23)
        )
    ]

    result = aggregate_daily_usage(transactions)

    assert len(result) == 1

    assert result[0]["usage_date"] == "2026-10-23"

    assert result[0]["quantity_used"] == "0.50"
