
from app.extensions import db


class InventoryItem(db.Model):
    __tablename__ = "inventory_items"

    id = db.Column(db.Integer, primary_key=True)

    sku = db.Column(
        db.String(30), unique=True, nullable=False
    )

    name = db.Column(
        db.String(120), nullable=False
    )

    category = db.Column(db.String(80))

    quantity = db.Column(
        db.Numeric(12, 2), nullable=False, default=0
    )

    unit = db.Column(
        db.String(20), nullable=False
    )

    reorder_level = db.Column(
        db.Numeric(12, 2), nullable=False, default=0
    )

    unit_cost = db.Column(
        db.Numeric(10, 2), nullable=False, default=0
    )
