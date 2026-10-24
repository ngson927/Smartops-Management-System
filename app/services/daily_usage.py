
from collections import defaultdict
from datetime import timezone
from decimal import Decimal
from zoneinfo import ZoneInfo


# ==========================================
# DAILY USAGE AGGREGATION
# ==========================================

def aggregate_daily_usage(
    transactions,
    timezone_name="America/New_York"
):

    daily_totals = defaultdict(
        lambda: Decimal("0.00")
    )

    local_timezone = ZoneInfo(timezone_name)

    for transaction in transactions:

        # Only count actual consumption
        if transaction.transaction_type != "OUT":
            continue

        quantity_change = Decimal(
            str(transaction.quantity_change)
        )

        # OUT transactions must reduce stock
        if (
            not quantity_change.is_finite()
            or quantity_change >= 0
        ):
            continue

        # ==================================
        # PREFER BUSINESS DATE
        # ==================================

        business_date = getattr(
            transaction,
            "business_date",
            None
        )

        if business_date is not None:

            usage_date = business_date

        else:

            # Older transactions may not have
            # a business date.

            timestamp = transaction.created_at

            if timestamp is None:
                continue

            # Existing database timestamps use UTC.
            if timestamp.tzinfo is None:

                timestamp = timestamp.replace(
                    tzinfo=timezone.utc
                )

            usage_date = timestamp.astimezone(
                local_timezone
            ).date()

        # Convert negative OUT to positive usage
        daily_totals[usage_date] += abs(
            quantity_change
        )

    # ======================================
    # PREPARE DAILY RESULTS
    # ======================================

    results = []

    for usage_date, quantity in sorted(
        daily_totals.items()
    ):

        results.append({
            "usage_date": usage_date.isoformat(),
            "quantity_used": str(
                quantity.quantize(
                    Decimal("0.01")
                )
            )
        })

    return results
