import json
from . import admin_bp
from .auth import admin_required
from flask import render_template
from extensions import db
from models.product import Product
from models.category import Category
from models.user import User
from upload_service import get_image_url

@admin_bp.get("/dashboard")
@admin_required
def admin_dashboard():
    # 1. Product Statistics
    products = Product.query.order_by(Product.id.desc()).all()
    total_products = len(products)
    total_stock_units = sum(p.stock for p in products)
    total_inventory_value = sum((float(p.price) * p.stock) for p in products)
    out_of_stock_products = [p for p in products if p.stock <= 0]
    low_stock_products = [p for p in products if 0 < p.stock <= 5]
    recent_products = products[:6]

    # 2. Category Statistics
    categories = Category.query.order_by(Category.name.asc()).all()
    total_categories = len(categories)

    # Chart data
    category_labels = [c.name for c in categories]
    category_product_counts = [len(c.products) if c.products else 0 for c in categories]
    category_stock_counts = [sum(p.stock for p in c.products) if c.products else 0 for c in categories]

    # 3. User Statistics
    users = User.query.order_by(User.id.desc()).all()
    total_users = len(users)
    admin_count = sum(1 for u in users if u.role == "admin")
    regular_user_count = total_users - admin_count
    recent_users = users[:6]

    # 4. Order Metrics (Persistent DB + Sync)
    from models.order import Order
    from .order import sync_users_dict_orders
    sync_users_dict_orders()

    db_orders = Order.query.order_by(Order.id.desc()).all()
    total_orders = len(db_orders)
    total_order_revenue = sum(o.total for o in db_orders if o.status != "Cancelled")
    pending_orders_count = sum(1 for o in db_orders if o.status == "Pending")
    recent_orders = db_orders[:6]

    return render_template(
        "admin/dashboard/admin.html",
        module="admin",
        total_products=total_products,
        total_stock_units=total_stock_units,
        total_inventory_value=total_inventory_value,
        out_of_stock_count=len(out_of_stock_products),
        out_of_stock_products=out_of_stock_products,
        low_stock_count=len(low_stock_products),
        low_stock_products=low_stock_products,
        total_categories=total_categories,
        category_labels_json=json.dumps(category_labels),
        category_product_counts_json=json.dumps(category_product_counts),
        category_stock_counts_json=json.dumps(category_stock_counts),
        total_users=total_users,
        admin_count=admin_count,
        regular_user_count=regular_user_count,
        recent_users=recent_users,
        recent_products=recent_products,
        total_orders=total_orders,
        total_order_revenue=total_order_revenue,
        pending_orders_count=pending_orders_count,
        recent_orders=recent_orders,
        get_image_url=get_image_url
    )