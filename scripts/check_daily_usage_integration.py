
import sys

from pathlib import Path
from decimal import Decimal


# ==========================================
# PROJECT IMPORTS
# ==========================================

project_root = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(project_root))


from app import create_app

from app.models import (
    InventoryItem,
    InventoryTransaction
)

from app.services.daily_usage import (
    aggregate_daily_usage
)


# ==========================================
# INTEGRATION TEST
# ==========================================

def check_daily_usage():

    app = create_app()

    app.config["TESTING"] = True

    # Disable login requirement for this
    # local test client only.
    # Does NOT change the running website.
    app.config["LOGIN_DISABLED"] = True

    with app.app_context():

        # Find our DEMO product
        item = InventoryItem.query.filter_by(
            sku="BLKTEA"
        ).first()

        if item is None:
            raise RuntimeError(
                "BLKTEA inventory item not found."
            )

        with app.test_client() as client:

            for source in ("DEMO", "REAL"):

                # ==================================
                # 1. READ RECORDS FROM MYSQL
                # ==================================

                transactions = (
                    InventoryTransaction.query.filter_by(
                        inventory_item_id=item.id,
                        transaction_type="OUT",
                        data_source=source
                    ).all()
                )

                # ==================================
                # 2. CALCULATE EXPECTED RESULTS
                # ==================================

                expected = aggregate_daily_usage(
                    transactions
                )

                expected_total = sum(
                    (
                        Decimal(row["quantity_used"])
                        for row in expected
                    ),
                    Decimal("0.00")
                )

                # ==================================
                # 3. CALL ACTUAL FLASK API
                # ==================================

                response = client.get(
                    f"/api/inventory/{item.id}/daily-usage"
                    f"?source={source}"
                )

                assert response.status_code == 200, (
                    f"{source}: API returned "
                    f"{response.status_code}"
                )

                data = response.get_json()

                # ==================================
                # 4. COMPARE API AGAINST MYSQL
                # ==================================

                assert data["data_source"] == source

                assert data["daily_usage"] == expected

                assert data["days_with_usage"] == len(
                    expected
                )

                assert Decimal(
                    data["total_usage"]
                ) == expected_total

                print(
                    f"{source}: PASS | "
                    f"{len(expected)} days | "
                    f"{expected_total:.2f} {item.unit}"
                )

    print(
        "\nSUCCESS: Flask API matches "
        "MySQL daily usage aggregation."
    )


if __name__ == "__main__":
    check_daily_usage()
