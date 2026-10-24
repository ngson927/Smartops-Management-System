
from decimal import Decimal

import pytest

from app.services.reorder import (
    calculate_reorder_recommendation
)


# ==========================================
# TEST 1: HEALTHY INVENTORY
# ==========================================

def test_stock_ok():

    result = calculate_reorder_recommendation(
        current_stock=20,
        average_daily_usage="0.40",
        lead_time_days=7,
        safety_stock=5,
        coverage_days=30
    )

    assert result["status"] == "STOCK_OK"

    assert result["needs_reorder"] is False

    assert result["reorder_point"] == Decimal("7.80")

    assert result["recommended_order_quantity"] == (
        Decimal("0.00")
    )

    assert result["days_until_reorder"] == (
        Decimal("30.50")
    )


# ==========================================
# TEST 2: LOW INVENTORY
# ==========================================

def test_reorder_required():

    result = calculate_reorder_recommendation(
        current_stock=6,
        average_daily_usage="0.40",
        lead_time_days=7,
        safety_stock=5,
        coverage_days=30
    )

    assert result["status"] == "REORDER_NOW"

    assert result["needs_reorder"] is True

    assert result["reorder_point"] == Decimal("7.80")

    assert result["target_stock"] == Decimal("19.80")

    assert result["recommended_order_quantity"] == (
        Decimal("13.80")
    )


# ==========================================
# TEST 3: EXACT REORDER POINT
# ==========================================

def test_exact_reorder_point():

    result = calculate_reorder_recommendation(
        current_stock="7.80",
        average_daily_usage="0.40",
        lead_time_days=7,
        safety_stock=5,
        coverage_days=30
    )

    assert result["needs_reorder"] is True

    assert result["days_until_reorder"] == (
        Decimal("0.00")
    )

    assert result["recommended_order_quantity"] == (
        Decimal("12.00")
    )


# ==========================================
# TEST 4: ZERO DAILY CONSUMPTION
# ==========================================

def test_zero_consumption():

    result = calculate_reorder_recommendation(
        current_stock=2,
        average_daily_usage=0,
        lead_time_days=7,
        safety_stock=5,
        coverage_days=30
    )

    assert result["needs_reorder"] is True

    assert result["recommended_order_quantity"] == (
        Decimal("3.00")
    )

    assert result["days_of_stock"] is None

    assert result["days_until_reorder"] is None


# ==========================================
# TEST 5: INVALID VALUES
# ==========================================

def test_negative_stock_rejected():

    with pytest.raises(ValueError):

        calculate_reorder_recommendation(
            current_stock=-5,
            average_daily_usage="0.40",
            lead_time_days=7,
            safety_stock=5
        )


def test_invalid_lead_time_rejected():

    with pytest.raises(ValueError):

        calculate_reorder_recommendation(
            current_stock=20,
            average_daily_usage="0.40",
            lead_time_days=-2,
            safety_stock=5
        )
