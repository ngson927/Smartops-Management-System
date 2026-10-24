
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.extensions import db


# ==========================================
# INVENTORY TRANSACTION MODEL
# ==========================================

class InventoryTransaction(db.Model):

    __tablename__ = "inventory_transactions"

    # Unique transaction ID
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # Related inventory item
    inventory_item_id = db.Column(
        db.Integer,
        db.ForeignKey("inventory_items.id"),
        nullable=False
    )

    # User recording transaction
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    # IN, OUT, WASTE, ADJUSTMENT
    transaction_type = db.Column(
        db.String(20),
        nullable=False
    )

    # Signed quantity change
    quantity_change = db.Column(
        db.Numeric(12, 2),
        nullable=False
    )

    # Stock before transaction
    quantity_before = db.Column(
        db.Numeric(12, 2),
        nullable=False
    )

    # Stock after transaction
    quantity_after = db.Column(
        db.Numeric(12, 2),
        nullable=False
    )

    # DEMO or REAL
    data_source = db.Column(
        db.String(10),
        nullable=False,
        server_default="DEMO"
    )

    # Actual business date of transaction
    # Nullable to preserve historical records
    business_date = db.Column(
        db.Date,
        nullable=True,
        default=lambda: datetime.now(
            ZoneInfo("America/New_York")
        ).date()
    )

    # Additional notes
    notes = db.Column(
        db.String(500),
        nullable=True
    )

    # UTC creation timestamp
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(
            timezone.utc
        ).replace(tzinfo=None)
    )

    __table_args__ = (

        db.CheckConstraint(
            "quantity_before >= 0",
            name="ck_transaction_before_nonnegative"
        ),

        db.CheckConstraint(
            "quantity_after >= 0",
            name="ck_transaction_after_nonnegative"
        ),

        db.CheckConstraint(
            "data_source IN ('DEMO', 'REAL')",
            name="ck_transaction_data_source"
        ),

        db.Index(
            "ix_transactions_item_created",
            "inventory_item_id",
            "created_at"
        ),

    )

    def __repr__(self):

        return (
            f"<InventoryTransaction "
            f"id={self.id} "
            f"type={self.transaction_type} "
            f"source={self.data_source} "
            f"change={self.quantity_change}>"
        )
