
from app.extensions import db


class InventoryUsage(db.Model):
    __tablename__ = "inventory_usage"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    inventory_item_id = db.Column(
        db.Integer,
        db.ForeignKey("inventory_items.id"),
        nullable=False,
        index=True
    )

    usage_date = db.Column(
        db.Date,
        nullable=False
    )

    quantity_used = db.Column(
        db.Numeric(12, 2),
        nullable=False
    )

    __table_args__ = (
        db.UniqueConstraint(
            "inventory_item_id",
            "usage_date",
            name="uq_inventory_usage_item_date"
        ),
    )
