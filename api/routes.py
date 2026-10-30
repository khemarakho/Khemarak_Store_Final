from flask import request, jsonify, session
from datetime import datetime, timezone
import uuid
from decimal import Decimal
from werkzeug.security import check_password_hash, generate_password_hash

from . import api_bp
from extensions import db, limiter
from models.user import User

# In-memory orders/auth cache
USERS = {}
from models.category import Category
from models.product import Product
from models.product_image import ProductImage
from notifications import send_telegram_message, send_product_photo

# ==========================================
# CORS HEADERS ON ALL API RESPONSES
# ==========================================
@api_bp.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
    return response


# ==========================================
# OPTIONS PRE-FLIGHT HANDLER
# ==========================================
@api_bp.route("/<path:path>", methods=["OPTIONS"])
@api_bp.route("/", methods=["OPTIONS"])
def api_options(path=""):
    return jsonify({"success": True}), 200


# ==========================================
# HEALTH CHECK
# ==========================================
@api_bp.get("/health")
def api_health():
    return jsonify({
        "success": True,
        "status": "healthy",
        "service": "Khemarak Store Core API",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })


# ==========================================
# CATEGORIES ENDPOINTS
# ==========================================
@api_bp.get("/categories")
def api_get_categories():
    categories = Category.query.order_by(Category.name.asc()).all()
    return jsonify({
        "success": True,
        "count": len(categories),
        "categories": [c.to_dict() for c in categories]
    })


@api_bp.get("/brands")
def get_brands():
    categories = Category.query.order_by(Category.name.asc()).all()
    brands_list = [
        {"name": c.name, "count": len(c.products) if c.products else 0}
        for c in categories
    ]

    return jsonify({
        "success": True,
        "brands": brands_list
    })


# ==========================================
# PRODUCTS ENDPOINTS (DATABASE POWERED)
# ==========================================
@api_bp.get("/products")
@limiter.limit("120 per minute")
def get_products():
    search = request.args.get("search", "").strip().lower()
    brand = request.args.get("brand", "").strip().lower()
    category_id = request.args.get("category_id", type=int)
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)
    sort_by = request.args.get("sort", "default")

    query = Product.query

    if category_id:
        query = query.filter(Product.category_id == category_id)
    elif brand and brand != "all":
        cat = Category.query.filter(Category.name.ilike(brand)).first()
        if cat:
            query = query.filter(Product.category_id == cat.id)

    if search:
        query = query.filter(
            (Product.name.ilike(f"%{search}%")) |
            (Product.description.ilike(f"%{search}%"))
        )

    if min_price is not None:
        query = query.filter(Product.price >= min_price)

    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    if sort_by == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort_by == "price_desc":
        query = query.order_by(Product.price.desc())
    elif sort_by == "name":
        query = query.order_by(Product.name.asc())
    else:
        query = query.order_by(Product.id.desc())

    all_results = query.all()
    total = len(all_results)

    page = max(1, request.args.get("page", 1, type=int))
    limit = max(1, min(100, request.args.get("limit", 20, type=int)))
    start = (page - 1) * limit
    paginated = all_results[start:start + limit]

    return jsonify({
        "success": True,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit if limit else 1,
        "products": [p.to_dict() for p in paginated]
    })


@api_bp.get("/products/<int:product_id>")
def get_product(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({"success": False, "error": "Product not found"}), 404

    related = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id
    ).limit(4).all()

    return jsonify({
        "success": True,
        "product": product.to_dict(),
        "related": [r.to_dict() for r in related]
    })


# ==========================================
# CART ENDPOINTS
# ==========================================
def _get_session_cart():
    if "cart" not in session:
        session["cart"] = []
    return session["cart"]


def _calculate_cart_totals(cart):
    subtotal = sum(item["price"] * item["quantity"] for item in cart)
    shipping = 0 if subtotal > 500 else (0 if subtotal == 0 else 15)
    tax = round(subtotal * 0.1, 2)
    total = round(subtotal + shipping + tax, 2)
    return {
        "item_count": sum(item["quantity"] for item in cart),
        "subtotal": subtotal,
        "shipping": shipping,
        "tax": tax,
        "total": total
    }


@api_bp.get("/cart")
def api_get_cart():
    cart = _get_session_cart()
    totals = _calculate_cart_totals(cart)
    return jsonify({
        "success": True,
        "cart": cart,
        "totals": totals
    })


@api_bp.post("/cart/add")
@limiter.limit("60 per minute")
def api_add_to_cart():
    data = request.get_json(silent=True) or request.form.to_dict()
    try:
        product_id = int(data.get("product_id"))
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "Invalid or missing product_id"}), 400

    quantity = int(data.get("quantity", 1))
    color = data.get("color", "")
    storage = data.get("storage", "")

    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({"success": False, "error": "Product not found"}), 404

    if product.stock <= 0:
        return jsonify({"success": False, "error": "Product is out of stock"}), 400

    name = product.name
    price = float(product.price)
    image = product.thumbnail

    cart = _get_session_cart()

    # Check if item with matching variant is already in cart
    for item in cart:
        if item["product_id"] == product_id and item.get("color") == color and item.get("storage") == storage:
            item["quantity"] += quantity
            session.modified = True
            totals = _calculate_cart_totals(cart)
            return jsonify({
                "success": True,
                "message": f"Updated quantity for {name}",
                "cart": cart,
                "totals": totals
            })

    cart.append({
        "product_id": product_id,
        "name": name,
        "price": price,
        "image": image,
        "quantity": quantity,
        "color": color,
        "storage": storage
    })
    session.modified = True
    totals = _calculate_cart_totals(cart)

    return jsonify({
        "success": True,
        "message": f"Added {name} to cart",
        "cart": cart,
        "totals": totals
    })


@api_bp.post("/cart/update")
@limiter.limit("60 per minute")
def api_update_cart():
    data = request.get_json(silent=True) or request.form.to_dict()
    cart = _get_session_cart()

    action = data.get("action")
    index = data.get("index")

    if index is None:
        return jsonify({"success": False, "error": "Missing item index"}), 400

    try:
        index = int(index)
    except ValueError:
        return jsonify({"success": False, "error": "Index must be an integer"}), 400

    if not (0 <= index < len(cart)):
        return jsonify({"success": False, "error": "Cart item not found"}), 404

    if action == "increase":
        cart[index]["quantity"] += 1
    elif action == "decrease":
        if cart[index]["quantity"] > 1:
            cart[index]["quantity"] -= 1
        else:
            cart.pop(index)
    elif action == "remove":
        cart.pop(index)
    elif action == "set":
        qty = int(data.get("quantity", 1))
        if qty <= 0:
            cart.pop(index)
        else:
            cart[index]["quantity"] = qty
    else:
        return jsonify({"success": False, "error": "Invalid action. Supported: increase, decrease, remove, set"}), 400

    session.modified = True
    totals = _calculate_cart_totals(cart)
    return jsonify({
        "success": True,
        "cart": cart,
        "totals": totals
    })


@api_bp.post("/cart/clear")
def api_clear_cart():
    session["cart"] = []
    session.modified = True
    return jsonify({
        "success": True,
        "message": "Cart cleared successfully",
        "cart": [],
        "totals": _calculate_cart_totals([])
    })


# ==========================================
# ORDERS & CHECKOUT ENDPOINTS
# ==========================================
@api_bp.post("/checkout")
@limiter.limit("10 per minute")
def api_checkout():
    data = request.get_json(silent=True) or request.form.to_dict()
    cart = _get_session_cart()

    if not cart:
        return jsonify({"success": False, "error": "Cannot checkout with an empty cart"}), 400

    fullname = data.get("fullname", "").strip()
    email = data.get("email", "").strip()
    phone = data.get("phone", "").strip()
    address = data.get("address", "").strip()
    city = data.get("city", "").strip()
    payment_method = data.get("payment", "Cash on Delivery")

    if not all([fullname, email, phone, address, city]):
        return jsonify({"success": False, "error": "Missing required shipping information"}), 400

    order_id = "ORD-" + str(uuid.uuid4())[:8].upper()
    totals = _calculate_cart_totals(cart)

    order_data = {
        "order_id": order_id,
        "order_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "customer_name": fullname,
        "customer_email": email,
        "customer_phone": phone,
        "shipping_address": address,
        "city": city,
        "payment_method": payment_method,
        "items": list(cart),
        "subtotal": totals["subtotal"],
        "shipping": totals["shipping"],
        "tax": totals["tax"],
        "total": totals["total"],
        "status": "Pending"
    }

    # Decrement stock in database
    for item in cart:
        prod_id = item.get("product_id")
        if prod_id:
            p = db.session.get(Product, prod_id)
            if p:
                p.stock = max(0, p.stock - item.get("quantity", 1))
    db.session.commit()

    # Record order in session and in USERS store
    if email not in USERS:
        USERS[email] = {
            "email": email,
            "name": fullname,
            "orders": []
        }
    if "orders" not in USERS[email]:
        USERS[email]["orders"] = []
    USERS[email]["orders"].append(order_data)

    session["last_order"] = order_data
    session["cart"] = []
    session.modified = True

    try:
        telegram_msg = f"""🛒 <b>NEW API ORDER</b>
━━━━━━━━━━━━━━
🆔 <b>Order ID:</b> {order_id}
👤 <b>Customer:</b> {fullname}
📧 <b>Email:</b> {email}
📞 <b>Phone:</b> {phone}
📍 <b>Address:</b> {address}, {city}
💳 <b>Payment:</b> {payment_method}
💰 <b>Total:</b> ${totals['total']:.2f}
📦 <b>Items:</b> {totals['item_count']} item(s)"""
        send_telegram_message(telegram_msg)
    except Exception as e:
        print("Telegram notification failure:", e)

    return jsonify({
        "success": True,
        "message": "Order placed successfully!",
        "order": order_data
    }), 201


@api_bp.get("/orders")
def api_get_orders():
    user = session.get("users")
    email = request.args.get("email") or (user.get("email") if user else None)
    if not email:
        return jsonify({"success": False, "error": "Please provide user email or log in"}), 401

    user_info = USERS.get(email, {})
    orders = user_info.get("orders", [])
    return jsonify({
        "success": True,
        "orders": orders
    })


@api_bp.get("/orders/<order_id>")
def api_get_order(order_id):
    for email, udata in USERS.items():
        for order in udata.get("orders", []):
            if order.get("order_id") == order_id:
                return jsonify({
                    "success": True,
                    "order": order
                })

    last_order = session.get("last_order")
    if last_order and last_order.get("order_id") == order_id:
        return jsonify({
            "success": True,
            "order": last_order
        })

    return jsonify({"success": False, "error": "Order not found"}), 404


# ==========================================
# AUTH ENDPOINTS
# ==========================================
@api_bp.post("/auth/login")
@limiter.limit("5 per minute; 20 per hour")
def api_login():
    data = request.get_json(silent=True) or request.form.to_dict()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"success": False, "error": "Email and password are required"}), 400

    db_user = User.query.filter_by(email=email).first()
    if db_user and check_password_hash(db_user.password, password):
        user_payload = {
            "id": db_user.id,
            "name": db_user.name,
            "email": db_user.email,
            "role": db_user.role
        }
        session["users"] = user_payload
        if db_user.role == "admin":
            session["user_id"] = db_user.id
            session["user_name"] = db_user.name
            session["user_email"] = db_user.email
            session["user_role"] = db_user.role
            session["logged_in"] = True

        return jsonify({
            "success": True,
            "message": "Login successful",
            "user": user_payload
        })

    if email in USERS and USERS[email].get("password") == password:
        user_info = USERS[email]
        user_payload = {
            "name": user_info.get("name"),
            "email": user_info.get("email"),
            "role": user_info.get("role", "user")
        }
        session["users"] = user_payload
        return jsonify({
            "success": True,
            "message": "Login successful",
            "user": user_payload
        })

    return jsonify({"success": False, "error": "Invalid email or password"}), 401


@api_bp.post("/auth/register")
@limiter.limit("5 per minute; 20 per hour")
def api_register():
    data = request.get_json(silent=True) or request.form.to_dict()
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password", "")

    if not name or not email or not password:
        return jsonify({"success": False, "error": "Name, email, and password are required"}), 400

    if User.query.filter_by(email=email).first() or email in USERS:
        return jsonify({"success": False, "error": "Email is already registered"}), 409

    hashed_pw = generate_password_hash(password)
    new_user = User(
        name=name,
        email=email,
        password=hashed_pw,
        role="user"
    )
    db.session.add(new_user)
    db.session.commit()

    USERS[email] = {
        "email": email,
        "password": password,
        "name": name,
        "role": "user",
        "created_at": datetime.now().strftime("%Y-%m-%d"),
        "orders": []
    }

    return jsonify({
        "success": True,
        "message": "Account created successfully!",
        "user": {
            "id": new_user.id,
            "name": name,
            "email": email,
            "role": "user"
        }
    }), 201


@api_bp.post("/auth/logout")
def api_logout():
    session.pop("users", None)
    return jsonify({
        "success": True,
        "message": "Logged out successfully"
    })


@api_bp.get("/auth/me")
def api_get_me():
    user = session.get("users")
    if not user:
        return jsonify({"success": False, "authenticated": False, "user": None}), 401
    return jsonify({
        "success": True,
        "authenticated": True,
        "user": user
    })
