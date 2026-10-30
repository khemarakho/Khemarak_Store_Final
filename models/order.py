import json
from datetime import datetime
from extensions import db


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    customer_name = db.Column(db.String(150), nullable=False)
    customer_email = db.Column(db.String(150), nullable=False, index=True)
    customer_phone = db.Column(db.String(50), nullable=True)
    shipping_address = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    payment_method = db.Column(db.String(50), default="Cash on Delivery")
    payment_status = db.Column(db.String(50), default="Pending")
    status = db.Column(db.String(50), default="Pending")  # Pending, Processing, Completed, Cancelled
    subtotal = db.Column(db.Float, default=0.0)
    shipping = db.Column(db.Float, default=0.0)
    tax = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, default=0.0)
    items_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def items(self):
        if not self.items_json:
            return []
        try:
            return json.loads(self.items_json)
        except Exception:
            return []

    @items.setter
    def items(self, val):
        self.items_json = json.dumps(val)

    def to_dict(self):
        order_date_str = self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else ""
        order_date_disp = self.created_at.strftime("%d %b %Y, %I:%M %p") if self.created_at else ""
        return {
            "id": self.id,
            "order_id": self.order_id,
            "customer_name": self.customer_name,
            "customer_email": self.customer_email,
            "customer_phone": self.customer_phone or "",
            "shipping_address": self.shipping_address or "",
            "city": self.city or "",
            "payment_method": self.payment_method or "Cash on Delivery",
            "payment_status": self.payment_status or "Pending",
            "status": self.status or "Pending",
            "subtotal": float(self.subtotal or 0.0),
            "shipping": float(self.shipping or 0.0),
            "tax": float(self.tax or 0.0),
            "total": float(self.total or 0.0),
            "items": self.items,
            "created_at": order_date_str,
            "order_date": order_date_str,
            "order_date_display": order_date_disp,
        }
