
from decimal import Decimal, InvalidOperation

from flask import (
    Blueprint,
    jsonify,
    render_template,
    request,
    flash,
    redirect,
    url_for
)

from flask_login import login_required
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import InventoryItem, InventoryUsage
from app.services.forecasting import calculate_forecast


inventory_bp = Blueprint("inventory", __name__)


# ==========================================
# 1. INVENTORY API - READ
# ==========================================

@inventory_bp.get("/api/inventory")
@login_required
def get_inventory():

    items = InventoryItem.query.order_by(
        InventoryItem.name
    ).all()

    result = []

    for item in items:
        result.append({
            "id": item.id,
            "sku": item.sku,
            "name": item.name,
            "category": item.category,
            "quantity": str(item.quantity),
            "unit": item.unit,
            "reorder_level": str(item.reorder_level),
            "unit_cost": str(item.unit_cost)
        })

    return jsonify(result)


# ==========================================
# 2. INVENTORY - CREATE
# ==========================================

@inventory_bp.route("/inventory/add", methods=["GET", "POST"])
@login_required
def add_inventory():

    if request.method == "POST":

        sku = request.form.get("sku", "").strip().upper()
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()
        unit = request.form.get("unit", "").strip()

        try:
            quantity = Decimal(
                request.form.get("quantity", "")
            )

            reorder_level = Decimal(
                request.form.get("reorder_level", "")
            )

            unit_cost = Decimal(
                request.form.get("unit_cost", "")
            )

        except (InvalidOperation, TypeError):
            flash("Please enter valid numbers.")
            return render_template(
                "inventory/add.html"
            ), 400

        values = (
            quantity,
            reorder_level,
            unit_cost
        )

        if (
            not sku
            or not name
            or not unit
            or len(sku) > 30
            or len(name) > 120
            or len(category) > 80
            or len(unit) > 20
            or any(
                not x.is_finite()
                or x < 0
                or x.as_tuple().exponent < -2
                for x in values
            )
            or quantity > Decimal("9999999999.99")
            or reorder_level > Decimal("9999999999.99")
            or unit_cost > Decimal("99999999.99")
        ):
            flash("Please check the values you entered.")
            return render_template(
                "inventory/add.html"
            ), 400

        item = InventoryItem(
            sku=sku,
            name=name,
            category=category or None,
            quantity=quantity,
            unit=unit,
            reorder_level=reorder_level,
            unit_cost=unit_cost
        )

        db.session.add(item)

        try:
            db.session.commit()

        except IntegrityError:
            db.session.rollback()
            flash("SKU already exists or could not be saved.")

        else:
            flash("Inventory item added successfully!")

            return redirect(
                url_for("inventory.add_inventory")
            )

    return render_template("inventory/add.html")


# ==========================================
# 3. INVENTORY DASHBOARD
# ==========================================

@inventory_bp.get("/inventory")
@login_required
def inventory_dashboard():

    # Retrieve inventory from MySQL
    items = InventoryItem.query.order_by(
        InventoryItem.name
    ).all()

    # Count inventory products
    total_items = len(items)

    # Count low-stock products
    low_stock_count = sum(
        1 for item in items
        if item.quantity <= item.reorder_level
    )

    # Calculate total stock value
    total_inventory_value = sum(
        (
            item.quantity * item.unit_cost
            for item in items
        ),
        Decimal("0.00")
    )

    return render_template(
        "inventory/list.html",
        items=items,
        total_items=total_items,
        low_stock_count=low_stock_count,
        total_inventory_value=total_inventory_value
    )



# ==========================================
# 4. INVENTORY - UPDATE WITH AUDIT HISTORY
# ==========================================

@inventory_bp.route(
    "/inventory/<int:item_id>/edit",
    methods=["GET", "POST"]
)
@login_required
def edit_inventory(item_id):

    from flask import abort
    from flask_login import current_user
    from sqlalchemy.exc import SQLAlchemyError
    from app.models import InventoryTransaction

    # ======================================
    # HANDLE FORM SUBMISSION
    # ======================================

    if request.method == "POST":

        try:
            quantity = Decimal(
                request.form.get("quantity", "")
            )

            reorder_level = Decimal(
                request.form.get("reorder_level", "")
            )

        except (InvalidOperation, TypeError):

            flash("Please enter valid numbers.")

            item = db.get_or_404(
                InventoryItem,
                item_id
            )

            return render_template(
                "inventory/edit.html",
                item=item
            ), 400

        # Validate values
        values = (quantity, reorder_level)

        if any(
            not x.is_finite()
            or x < 0
            or x > Decimal("9999999999.99")
            or x.as_tuple().exponent < -2
            for x in values
        ):

            flash(
                "Please enter valid non-negative "
                "values (up to 2 decimals)."
            )

            item = db.get_or_404(
                InventoryItem,
                item_id
            )

            return render_template(
                "inventory/edit.html",
                item=item
            ), 400

        # ======================================
        # UPDATE INVENTORY ATOMICALLY
        # ======================================

        try:

            # Lock the inventory row
            item = db.session.execute(
                db.select(InventoryItem)
                .where(
                    InventoryItem.id == item_id
                )
                .with_for_update()
            ).scalar_one_or_none()

            if item is None:
                db.session.rollback()
                abort(404)

            # Current stored values
            quantity_before = Decimal(
                item.quantity
            )

            reorder_before = Decimal(
                item.reorder_level
            )

            # ======================================
            # RECORD STOCK ADJUSTMENT
            # ======================================

            if quantity != quantity_before:

                quantity_change = (
                    quantity - quantity_before
                )

                transaction = InventoryTransaction(
                    inventory_item_id=item.id,
                    user_id=current_user.id,
                    transaction_type="ADJUSTMENT",
                    quantity_change=quantity_change,
                    quantity_before=quantity_before,
                    quantity_after=quantity,
                    notes="Stock adjusted via Edit Inventory"
                )

                db.session.add(transaction)

            # ======================================
            # UPDATE INVENTORY VALUES
            # ======================================

            item.quantity = quantity
            item.reorder_level = reorder_level

            # Commit inventory and history together
            db.session.commit()

        except SQLAlchemyError:

            db.session.rollback()

            flash(
                "Unable to update inventory. "
                "Please try again."
            )

            return redirect(
                url_for(
                    "inventory.edit_inventory",
                    item_id=item_id
                )
            )

        if quantity != quantity_before:
            flash(
                "Inventory updated and adjustment "
                "recorded successfully!"
            )

        elif reorder_level != reorder_before:
            flash(
                "Reorder level updated successfully!"
            )

        else:
            flash("No changes were made.")

        return redirect(
            url_for(
                "inventory.inventory_dashboard"
            )
        )

    # ======================================
    # DISPLAY EDIT FORM
    # ======================================

    item = db.get_or_404(
        InventoryItem,
        item_id
    )

    return render_template(
        "inventory/edit.html",
        item=item
    )



# ==========================================
# 5. ANALYTICS API - GROUP BY CATEGORY
# ==========================================

@inventory_bp.get("/api/analytics/inventory-by-category")
@login_required
def inventory_by_category():

    results = db.session.query(
        InventoryItem.category,

        func.count(
            InventoryItem.id
        ).label("total_items"),

        func.sum(
            InventoryItem.quantity
            * InventoryItem.unit_cost
        ).label("total_value")

    ).group_by(
        InventoryItem.category
    ).all()

    data = []

    for row in results:
        data.append({
            "category": row.category,
            "total_items": row.total_items,
            "total_value": str(row.total_value)
        })

    return jsonify(data)


# ==========================================
# 6. ANALYTICS DASHBOARD
# ==========================================

@inventory_bp.get("/analytics")
@login_required
def analytics_dashboard():

    return render_template(
        "inventory/analytics.html"
    )


# ==========================================
# 7. FORECASTING API
# ==========================================

@inventory_bp.get("/api/forecast/<int:item_id>")
@login_required
def get_forecast(item_id):

    # Find inventory item
    item = db.get_or_404(
        InventoryItem,
        item_id
    )

    # Retrieve historical usage
    records = InventoryUsage.query.filter_by(
        inventory_item_id=item.id
    ).order_by(
        InventoryUsage.usage_date
    ).all()

    # Calculate demand forecast
    forecast = calculate_forecast(
        records,
        item.quantity
    )

    # Handle insufficient data
    if forecast is None:

        return jsonify({
            "error": (
                "At least 7 consecutive days "
                "of usage are required."
            )
        }), 422

    # Convert Decimal values for JSON
    result = {
        key: (
            str(value)
            if isinstance(value, Decimal)
            else value
        )
        for key, value in forecast.items()
    }

    # Add inventory information
    result["sku"] = item.sku
    result["item_name"] = item.name
    result["unit"] = item.unit

    return jsonify(result)


# ==========================================
# 8. FORECASTING DASHBOARD - NEW
# ==========================================

@inventory_bp.get("/forecast/<int:item_id>")
@login_required
def forecast_dashboard(item_id):

    # Retrieve inventory item
    item = db.get_or_404(
        InventoryItem,
        item_id
    )

    # Display forecasting dashboard
    return render_template(
        "inventory/forecast.html",
        item=item
    )


# ==========================================
# 9. MACHINE LEARNING EVALUATION API
# ==========================================

@inventory_bp.get("/api/ml-evaluation")
@login_required
def get_ml_evaluation():

    import json
    from pathlib import Path
    from flask import current_app

    # Locate saved ML evaluation results
    project_root = Path(current_app.root_path).parent

    file_path = (
        project_root / "data" / "ml_evaluation.json"
    )

    # Load the JSON file
    try:
        with file_path.open("r", encoding="utf-8") as file:
            evaluation_data = json.load(file)

    except FileNotFoundError:
        return jsonify({
            "error": "ML evaluation data not found."
        }), 404

    except (OSError, json.JSONDecodeError):
        current_app.logger.exception(
            "Failed to load ML evaluation data"
        )

        return jsonify({
            "error": "Unable to load ML evaluation data."
        }), 500

    # Return ML results as JSON
    return jsonify(evaluation_data)


# ==========================================
# 10. MACHINE LEARNING EVALUATION DASHBOARD
# ==========================================

@inventory_bp.get("/ml-evaluation")
@login_required
def ml_evaluation_dashboard():

    return render_template(
        "inventory/ml_evaluation.html"
    )


# ==========================================
# 11. INVENTORY TRANSACTIONS
# ==========================================

@inventory_bp.route(
    "/inventory/transactions",
    methods=["GET", "POST"]
)
@login_required
def inventory_transactions():

    from datetime import date, datetime
    from zoneinfo import ZoneInfo

    from flask_login import current_user
    from sqlalchemy.exc import SQLAlchemyError

    from app.models import InventoryTransaction

    # ======================================
    # STORE LOCAL DATE
    # ======================================

    store_today_date = datetime.now(
        ZoneInfo("America/New_York")
    ).date()

    store_today = store_today_date.isoformat()

    # ======================================
    # HANDLE NEW TRANSACTION
    # ======================================

    if request.method == "POST":

        item_id_raw = request.form.get(
            "item_id", ""
        ).strip()

        transaction_type = request.form.get(
            "transaction_type", ""
        ).strip().upper()

        quantity_raw = request.form.get(
            "quantity", ""
        ).strip()

        business_date_raw = request.form.get(
            "business_date", ""
        ).strip()

        notes = request.form.get(
            "notes", ""
        ).strip()

        # ==================================
        # VALIDATE ITEM ID
        # ==================================

        try:
            item_id = int(item_id_raw)

            if item_id <= 0:
                raise ValueError

        except (ValueError, TypeError):

            flash("Please select a valid inventory item.")

            return redirect(
                url_for("inventory.inventory_transactions")
            )

        # ==================================
        # VALIDATE TRANSACTION TYPE
        # ==================================

        valid_types = {
            "IN",
            "OUT",
            "WASTE",
            "ADJUSTMENT"
        }

        if transaction_type not in valid_types:

            flash("Please select a valid transaction type.")

            return redirect(
                url_for("inventory.inventory_transactions")
            )

        # ==================================
        # VALIDATE QUANTITY
        # ==================================

        try:
            quantity = Decimal(quantity_raw)

        except (InvalidOperation, TypeError):

            flash("Please enter a valid quantity.")

            return redirect(
                url_for("inventory.inventory_transactions")
            )

        max_quantity = Decimal("9999999999.99")

        if (
            not quantity.is_finite()
            or quantity < 0
            or quantity > max_quantity
            or quantity.as_tuple().exponent < -2
        ):

            flash(
                "Please enter a valid non-negative "
                "quantity with up to 2 decimals."
            )

            return redirect(
                url_for("inventory.inventory_transactions")
            )

        # IN, OUT and WASTE require a positive quantity.
        # ADJUSTMENT may set stock to zero.

        if transaction_type != "ADJUSTMENT" and quantity == 0:

            flash("Transaction quantity must be greater than zero.")

            return redirect(
                url_for("inventory.inventory_transactions")
            )

        # ==================================
        # VALIDATE BUSINESS DATE
        # ==================================

        try:
            selected_business_date = date.fromisoformat(
                business_date_raw
            )

        except (ValueError, TypeError):

            flash("Please enter a valid business date.")

            return redirect(
                url_for("inventory.inventory_transactions")
            )

        if selected_business_date > store_today_date:

            flash("Business date cannot be in the future.")

            return redirect(
                url_for("inventory.inventory_transactions")
            )

        # ==================================
        # VALIDATE NOTES
        # ==================================

        if len(notes) > 500:

            flash("Notes cannot exceed 500 characters.")

            return redirect(
                url_for("inventory.inventory_transactions")
            )

        # ==================================
        # DATABASE TRANSACTION
        # ==================================

        try:

            # Lock inventory row during update
            item = db.session.execute(
                db.select(InventoryItem)
                .where(InventoryItem.id == item_id)
                .with_for_update()
            ).scalar_one_or_none()

            if item is None:

                db.session.rollback()

                flash("Inventory item not found.")

                return redirect(
                    url_for("inventory.inventory_transactions")
                )

            quantity_before = Decimal(item.quantity)

            # ==================================
            # CALCULATE NEW STOCK
            # ==================================

            if transaction_type == "IN":

                quantity_after = quantity_before + quantity

            elif transaction_type in {"OUT", "WASTE"}:

                quantity_after = quantity_before - quantity

            else:

                # ADJUSTMENT is the actual counted stock
                quantity_after = quantity

            # ==================================
            # PREVENT INVALID STOCK
            # ==================================

            if quantity_after < 0:

                db.session.rollback()

                flash(
                    "Insufficient stock. Transaction "
                    "would result in negative inventory."
                )

                return redirect(
                    url_for("inventory.inventory_transactions")
                )

            if quantity_after > max_quantity:

                db.session.rollback()

                flash("Resulting stock exceeds the allowed limit.")

                return redirect(
                    url_for("inventory.inventory_transactions")
                )

            quantity_change = (
                quantity_after - quantity_before
            )

            if quantity_change == 0:

                db.session.rollback()

                flash("Transaction does not change stock.")

                return redirect(
                    url_for("inventory.inventory_transactions")
                )

            # ==================================
            # UPDATE INVENTORY
            # ==================================

            item.quantity = quantity_after

            # ==================================
            # SAVE TRANSACTION HISTORY
            # ==================================

            transaction = InventoryTransaction(
                inventory_item_id=item.id,
                user_id=current_user.id,
                transaction_type=transaction_type,
                quantity_change=quantity_change,
                quantity_before=quantity_before,
                quantity_after=quantity_after,

                # NEW: actual business date
                business_date=selected_business_date,

                # Keep current database in demo mode
                data_source="DEMO",

                notes=notes or None
            )

            db.session.add(transaction)

            # Stock and transaction history saved together
            db.session.commit()

        except SQLAlchemyError:

            db.session.rollback()

            flash(
                "Unable to save transaction. "
                "Please try again."
            )

            return redirect(
                url_for("inventory.inventory_transactions")
            )

        flash("Inventory transaction recorded successfully!")

        return redirect(
            url_for("inventory.inventory_transactions")
        )

    # ======================================
    # DISPLAY TRANSACTION DASHBOARD
    # ======================================

    items = InventoryItem.query.order_by(
        InventoryItem.name
    ).all()

    transactions = InventoryTransaction.query.order_by(
        InventoryTransaction.created_at.desc(),
        InventoryTransaction.id.desc()
    ).limit(50).all()

    item_names = {
        item.id: item.name
        for item in items
    }

    return render_template(
        "inventory/transactions.html",
        items=items,
        transactions=transactions,
        item_names=item_names,
        store_today=store_today
    )


# ==========================================
# 12. DAILY INVENTORY USAGE API
# ==========================================

@inventory_bp.get(
    "/api/inventory/<int:item_id>/daily-usage"
)
@login_required
def get_daily_usage(item_id):

    from app.models import InventoryTransaction
    from app.services.daily_usage import aggregate_daily_usage

    # 1. Find inventory item
    item = db.get_or_404(
        InventoryItem,
        item_id
    )

    # 2. Select data source
    # Default to DEMO until real-data workflow is ready
    source = request.args.get(
        "source",
        "DEMO"
    ).strip().upper()

    if source not in {"DEMO", "REAL"}:

        return jsonify({
            "error": "Source must be DEMO or REAL."
        }), 400

    # 3. Retrieve matching consumption transactions
    transactions = InventoryTransaction.query.filter_by(
        inventory_item_id=item.id,
        transaction_type="OUT",
        data_source=source
    ).order_by(
        InventoryTransaction.created_at,
        InventoryTransaction.id
    ).all()

    # 4. Aggregate consumption by local date
    daily_usage = aggregate_daily_usage(
        transactions,
        timezone_name="America/New_York"
    )

    # 5. Calculate total consumption
    total_usage = sum(
        (
            Decimal(day["quantity_used"])
            for day in daily_usage
        ),
        Decimal("0.00")
    )

    # 6. Return API response
    return jsonify({
        "item_id": item.id,
        "sku": item.sku,
        "item_name": item.name,
        "unit": item.unit,
        "data_source": source,
        "timezone": "America/New_York",
        "days_with_usage": len(daily_usage),
        "total_usage": str(total_usage),
        "daily_usage": daily_usage
    })


# ==========================================
# 13. SMART REORDER RECOMMENDATION API
# ==========================================

@inventory_bp.get("/api/reorder/<int:item_id>")
@login_required
def get_reorder_recommendation(item_id):

    from app.services.reorder import (
        calculate_reorder_recommendation
    )

    # 1. Find inventory item
    item = db.get_or_404(
        InventoryItem,
        item_id
    )

    # 2. Read planning parameters
    # These are DEMO defaults, not actual supplier settings.
    try:
        lead_time_days = int(
            request.args.get("lead_time_days", "7")
        )

        safety_stock = Decimal(
            request.args.get("safety_stock", "5")
        )

        coverage_days = int(
            request.args.get("coverage_days", "30")
        )

    except (ValueError, InvalidOperation, TypeError):
        return jsonify({
            "error": "Invalid reorder parameters."
        }), 400

    # 3. Validate planning parameters
    if (
        not 0 <= lead_time_days <= 365
        or not 1 <= coverage_days <= 365
        or not safety_stock.is_finite()
        or safety_stock < 0
        or safety_stock > Decimal("99999999.99")
    ):
        return jsonify({
            "error": "Reorder parameters are out of range."
        }), 400

    # 4. Retrieve historical usage records
    # IMPORTANT: Existing InventoryUsage records
    # are DEMO data, not verified real consumption.
    records = InventoryUsage.query.filter_by(
        inventory_item_id=item.id
    ).order_by(
        InventoryUsage.usage_date
    ).all()

    # 5. Calculate average daily usage
    forecast = calculate_forecast(
        records,
        item.quantity
    )

    if forecast is None:
        return jsonify({
            "error": (
                "At least 7 consecutive days "
                "of usage are required."
            )
        }), 422

    # 6. Calculate reorder recommendation
    try:
        recommendation = calculate_reorder_recommendation(
            current_stock=item.quantity,
            average_daily_usage=forecast[
                "average_daily_usage"
            ],
            lead_time_days=lead_time_days,
            safety_stock=safety_stock,
            coverage_days=coverage_days
        )

    except ValueError as error:
        return jsonify({
            "error": str(error)
        }), 400

    # 7. Convert Decimal values to JSON strings
    result = {
        key: (
            str(value)
            if isinstance(value, Decimal)
            else value
        )
        for key, value in recommendation.items()
    }

    # 8. Add item and data information
    result["item_id"] = item.id
    result["sku"] = item.sku
    result["item_name"] = item.name
    result["unit"] = item.unit

    result["data_source"] = "DEMO"
    result["forecast_method"] = "7-day moving average"
    result["as_of_date"] = forecast["as_of_date"]

    result["disclaimer"] = (
        "Illustrative recommendation using demo "
        "usage data and planning assumptions. "
        "Not a verified purchasing recommendation."
    )

    return jsonify(result)


# ==========================================
# 14. BUSINESS INSIGHTS DASHBOARD
# ==========================================

@inventory_bp.get("/insights")
@login_required
def business_insights_dashboard():

    from app.services.reorder import (
        calculate_reorder_recommendation
    )

    # Load products from MySQL
    items = InventoryItem.query.order_by(
        InventoryItem.name
    ).all()

    insights = []

    total_inventory_value = Decimal("0.00")
    reorder_now_count = 0
    insufficient_data_count = 0
    low_stock_count = 0

    # Temporary DEMO planning assumptions
    lead_time_days = 7
    coverage_days = 30

    for item in items:

        # Inventory valuation
        total_inventory_value += (
            item.quantity * item.unit_cost
        )

        # Existing low-stock threshold
        low_stock = (
            item.quantity <= item.reorder_level
        )

        if low_stock:
            low_stock_count += 1

        # Read the historical usage records
        # These are currently DEMO data
        usage_records = InventoryUsage.query.filter_by(
            inventory_item_id=item.id
        ).order_by(
            InventoryUsage.usage_date
        ).all()

        forecast = calculate_forecast(
            usage_records,
            item.quantity
        )

        recommendation = None

        # Do NOT interpret missing data as safe stock
        if forecast is None:

            status = "NEEDS_HISTORY"
            insufficient_data_count += 1

        else:

            # DEMO assumption:
            # Use current reorder level as safety stock.
            # Real businesses should configure this
            # independently for each supplier/product.
            recommendation = (
                calculate_reorder_recommendation(
                    current_stock=item.quantity,
                    average_daily_usage=forecast[
                        "average_daily_usage"
                    ],
                    lead_time_days=lead_time_days,
                    safety_stock=item.reorder_level,
                    coverage_days=coverage_days
                )
            )

            status = recommendation["status"]

            if status == "REORDER_NOW":
                reorder_now_count += 1

        insights.append({
            "item": item,
            "status": status,
            "low_stock": low_stock,
            "forecast": forecast,
            "recommendation": recommendation
        })

    # Display urgent items first, missing data last
    priority = {
        "REORDER_NOW": 0,
        "STOCK_OK": 1,
        "NEEDS_HISTORY": 2
    }

    insights.sort(
        key=lambda row: priority.get(
            row["status"], 3
        )
    )

    return render_template(
        "inventory/business_insights.html",
        insights=insights,
        total_items=len(items),
        total_inventory_value=total_inventory_value,
        reorder_now_count=reorder_now_count,
        insufficient_data_count=insufficient_data_count,
        low_stock_count=low_stock_count,
        lead_time_days=lead_time_days,
        coverage_days=coverage_days
    )


# ==========================================
# 15. REAL CONSUMPTION FORECAST API
# ==========================================

@inventory_bp.get("/api/forecast/real/<int:item_id>")
@login_required
def get_real_forecast(item_id):

    from datetime import date
    from types import SimpleNamespace

    from app.models import InventoryTransaction
    from app.services.daily_usage import aggregate_daily_usage

    # 1. Find inventory item
    item = db.get_or_404(
        InventoryItem,
        item_id
    )

    # 2. Get REAL consumption transactions only
    transactions = InventoryTransaction.query.filter_by(
        inventory_item_id=item.id,
        transaction_type="OUT",
        data_source="REAL"
    ).order_by(
        InventoryTransaction.created_at,
        InventoryTransaction.id
    ).all()

    # 3. Aggregate consumption by store-local date
    daily_usage = aggregate_daily_usage(
        transactions,
        timezone_name="America/New_York"
    )

    # 4. Convert daily totals to forecasting records
    records = []

    for row in daily_usage:

        records.append(
            SimpleNamespace(
                usage_date=date.fromisoformat(
                    row["usage_date"]
                ),
                quantity_used=Decimal(
                    row["quantity_used"]
                )
            )
        )

    # 5. Calculate forecast using REAL records only
    forecast = calculate_forecast(
        records,
        item.quantity
    )

    # 6. Insufficient data
    if forecast is None:

        return jsonify({
            "status": "INSUFFICIENT_REAL_DATA",
            "data_source": "REAL",
            "item_name": item.name,
            "days_with_usage": len(records),
            "error": (
                "At least 7 consecutive days "
                "with recorded consumption are required."
            )
        }), 422

    # 7. Convert Decimal values to JSON
    result = {
        key: (
            str(value)
            if isinstance(value, Decimal)
            else value
        )
        for key, value in forecast.items()
    }

    result.update({
        "item_id": item.id,
        "sku": item.sku,
        "item_name": item.name,
        "unit": item.unit,
        "data_source": "REAL",
        "forecast_method": "7-day moving average",
        "days_with_usage": len(records),
        "note": (
            "Uses only REAL-tagged OUT transactions. "
            "Missing days are not assumed to have zero usage. "
            "Source labeling alone does not verify accuracy."
        )
    })

    return jsonify(result)
