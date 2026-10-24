
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


# ==========================================
# SMARTOPS - SMART REORDER ENGINE
# ==========================================

TWO_DECIMALS = Decimal("0.01")


def calculate_reorder_recommendation(
    current_stock,
    average_daily_usage,
    lead_time_days,
    safety_stock,
    coverage_days=30
):
    """
    Calculate when and how much inventory to reorder.

    current_stock:
        Current available inventory quantity.

    average_daily_usage:
        Estimated daily inventory consumption.

    lead_time_days:
        Days required for supplier delivery.

    safety_stock:
        Extra inventory kept as a buffer.

    coverage_days:
        Desired inventory coverage after delivery.

    Returns:
        Reorder point, order quantity, stock coverage,
        and estimated time until reordering.
    """

    # ======================================
    # 1. CONVERT INPUTS TO DECIMAL
    # ======================================

    try:
        stock = Decimal(str(current_stock))
        daily_usage = Decimal(str(average_daily_usage))
        safety = Decimal(str(safety_stock))

    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("Invalid inventory quantities.")

    # ======================================
    # 2. VALIDATE INPUTS
    # ======================================

    for value in (stock, daily_usage, safety):

        if not value.is_finite() or value < 0:
            raise ValueError(
                "Inventory quantities must be "
                "finite and non-negative."
            )

    if (
        isinstance(lead_time_days, bool)
        or not isinstance(lead_time_days, int)
        or lead_time_days < 0
    ):
        raise ValueError(
            "Lead time must be a non-negative integer."
        )

    if (
        isinstance(coverage_days, bool)
        or not isinstance(coverage_days, int)
        or coverage_days <= 0
    ):
        raise ValueError(
            "Coverage days must be a positive integer."
        )

    # ======================================
    # 3. CALCULATE REORDER POINT
    # ======================================

    expected_lead_time_demand = (
        daily_usage * lead_time_days
    )

    reorder_point = (
        expected_lead_time_demand + safety
    )

    # ======================================
    # 4. CALCULATE TARGET STOCK
    # ======================================

    target_stock = (
        daily_usage * (lead_time_days + coverage_days)
        + safety
    )

    # ======================================
    # 5. DETERMINE REORDER STATUS
    # ======================================

    needs_reorder = stock <= reorder_point

    if needs_reorder:
        quantity_to_order = max(
            Decimal("0"),
            target_stock - stock
        )
    else:
        quantity_to_order = Decimal("0")

    # ======================================
    # 6. ESTIMATE DAYS REMAINING
    # ======================================

    if daily_usage > 0:

        days_of_stock = stock / daily_usage

        days_until_reorder = max(
            Decimal("0"),
            (stock - reorder_point) / daily_usage
        )

    else:

        # No observed demand
        days_of_stock = None
        days_until_reorder = None

    # ======================================
    # 7. GENERATE BUSINESS STATUS
    # ======================================

    if needs_reorder:
        status = "REORDER_NOW"
    else:
        status = "STOCK_OK"

    # ======================================
    # 8. ROUND OUTPUT VALUES
    # ======================================

    def round_decimal(value):

        if value is None:
            return None

        return value.quantize(
            TWO_DECIMALS,
            rounding=ROUND_HALF_UP
        )

    return {
        "status": status,
        "needs_reorder": needs_reorder,
        "current_stock": round_decimal(stock),
        "average_daily_usage": round_decimal(daily_usage),
        "lead_time_days": lead_time_days,
        "coverage_days": coverage_days,
        "safety_stock": round_decimal(safety),
        "reorder_point": round_decimal(reorder_point),
        "target_stock": round_decimal(target_stock),
        "recommended_order_quantity": round_decimal(
            quantity_to_order
        ),
        "days_of_stock": round_decimal(days_of_stock),
        "days_until_reorder": round_decimal(
            days_until_reorder
        )
    }
