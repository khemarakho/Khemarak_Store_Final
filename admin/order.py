from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, jsonify
from extensions import db
from models.order import Order
from . import admin_bp
from .auth import admin_required


def sync_users_dict_orders():
    """Sync any in-memory orders from USERS dict to SQLite database."""
    try:
        from app import USERS
        for email, udata in USERS.items():
            if isinstance(udata, dict) and "orders" in udata:
                for ord_data in udata["orders"]:
                    if not isinstance(ord_data, dict):
                        continue
                    oid = ord_data.get("order_id")
                    if not oid:
                        continue
                    existing = Order.query.filter_by(order_id=oid).first()
                    if not existing:
                        new_o = Order(
                            order_id=oid,
                            customer_name=ord_data.get("customer_name") or udata.get("name", "Customer"),
                            customer_email=ord_data.get("customer_email") or email,
                            customer_phone=ord_data.get("customer_phone", ""),
                            shipping_address=ord_data.get("shipping_address", ""),
                            city=ord_data.get("city", ""),
                            payment_method=ord_data.get("payment_method", "Cash on Delivery"),
                            payment_status=ord_data.get("payment_status", "Pending"),
                            status=ord_data.get("status", "Pending").capitalize(),
                            subtotal=float(ord_data.get("subtotal", 0.0)),
                            shipping=float(ord_data.get("shipping", 0.0)),
                            tax=float(ord_data.get("tax", 0.0)),
                            total=float(ord_data.get("total", 0.0)),
                            items=ord_data.get("items", [])
                        )
                        db.session.add(new_o)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print("Order sync error:", e)


@admin_bp.route("/orders", methods=["GET"])
@admin_required
def admin_orders():
    # Sync memory orders if any
    sync_users_dict_orders()

    status_filter = request.args.get("status", "all").strip().lower()
    search_query = request.args.get("q", "").strip()

    query = Order.query

    if status_filter and status_filter != "all":
        query = query.filter(db.func.lower(Order.status) == status_filter)

    if search_query:
        search_pattern = f"%{search_query}%"
        query = query.filter(
            db.or_(
                Order.order_id.ilike(search_pattern),
                Order.customer_name.ilike(search_pattern),
                Order.customer_email.ilike(search_pattern),
                Order.customer_phone.ilike(search_pattern),
                Order.city.ilike(search_pattern)
            )
        )

    orders = query.order_by(Order.id.desc()).all()

    # Aggregate Statistics
    all_orders = Order.query.all()
    total_orders_count = len(all_orders)
    total_revenue = sum(o.total for o in all_orders if o.status != "Cancelled")
    pending_count = sum(1 for o in all_orders if o.status == "Pending")
    processing_count = sum(1 for o in all_orders if o.status == "Processing")
    completed_count = sum(1 for o in all_orders if o.status == "Completed")
    cancelled_count = sum(1 for o in all_orders if o.status == "Cancelled")

    return render_template(
        "admin/order/orders.html",
        module="orders",
        orders=orders,
        status_filter=status_filter,
        search_query=search_query,
        total_orders_count=total_orders_count,
        total_revenue=total_revenue,
        pending_count=pending_count,
        processing_count=processing_count,
        completed_count=completed_count,
        cancelled_count=cancelled_count
    )


@admin_bp.route("/orders/<int:order_id>/status", methods=["POST"])
@admin_required
def admin_order_update_status(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        flash("Order not found.", "danger")
        return redirect(url_for("admin.admin_orders"))

    new_status = request.form.get("status", "").strip().capitalize()
    valid_statuses = ["Pending", "Processing", "Completed", "Cancelled"]
    if new_status in valid_statuses:
        order.status = new_status
        if new_status == "Completed":
            order.payment_status = "Paid"
        db.session.commit()

        # Update in-memory dict if present
        try:
            from app import USERS
            for u in USERS.values():
                if isinstance(u, dict) and "orders" in u:
                    for o in u["orders"]:
                        if isinstance(o, dict) and o.get("order_id") == order.order_id:
                            o["status"] = new_status
        except Exception:
            pass

        flash(f"Order #{order.order_id} status updated to {new_status}.", "success")
    else:
        flash("Invalid status specified.", "warning")

    return redirect(request.referrer or url_for("admin.admin_orders"))


@admin_bp.route("/orders/<int:order_id>/delete", methods=["POST"])
@admin_required
def admin_order_delete(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        flash("Order not found.", "danger")
        return redirect(url_for("admin.admin_orders"))

    oid = order.order_id
    db.session.delete(order)
    db.session.commit()

    # Remove from in-memory USERS dict as well
    try:
        from app import USERS
        for u in USERS.values():
            if isinstance(u, dict) and "orders" in u:
                u["orders"] = [o for o in u["orders"] if isinstance(o, dict) and o.get("order_id") != oid]
    except Exception:
        pass

    flash(f"Order #{oid} deleted successfully.", "success")
    return redirect(url_for("admin.admin_orders"))


@admin_bp.route("/orders/<int:order_id>/json", methods=["GET"])
@admin_required
def admin_order_json(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({"success": False, "error": "Order not found"}), 404
    return jsonify({"success": True, "order": order.to_dict()})
