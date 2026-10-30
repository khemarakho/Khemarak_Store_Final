import os
import uuid
from functools import wraps
from datetime import datetime
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    session,
    current_app,
    send_from_directory
)
from flask_wtf.csrf import CSRFError
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db, migrate, csrf, limiter, cors
from config import config
from models.user import User
from models.category import Category
from models.product import Product
from models.product_image import ProductImage
from models.order import Order
from admin import admin_bp
from admin.auth import admin_required
from api import api_bp
from notifications import send_telegram_message, send_product_photo
from upload_service import get_image_url

# In-memory user cache fallback
USERS = {}

app = Flask(__name__)
app.config.from_object(config)

# ==========================================
# INITIALIZE EXTENSIONS
# ==========================================
db.init_app(app)
migrate.init_app(app, db)
csrf.init_app(app)
limiter.init_app(app)
cors.init_app(
    app,
    resources={r"/api/*": {"origins": "*"}},
    supports_credentials=True
)

# CSRF exemption for REST API (APIs use JSON, tokens, and CORS)
csrf.exempt(api_bp)

# ==========================================
# REGISTER BLUEPRINTS
# ==========================================
app.register_blueprint(admin_bp)
app.register_blueprint(api_bp)

with app.app_context():
    db.create_all()

# ==========================================
# ERROR HANDLERS
# ==========================================
@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    if request.is_json or request.path.startswith("/api/"):
        return jsonify({
            "success": False,
            "error": "CSRF token missing or invalid",
            "message": e.description
        }), 400
    flash("Your session security token has expired. Please try submitting again.", "warning")
    return redirect(request.referrer or url_for("index"))


@app.errorhandler(429)
def handle_ratelimit_error(e):
    if request.is_json or request.path.startswith("/api/"):
        return jsonify({
            "success": False,
            "error": "Rate limit exceeded",
            "message": str(e.description)
        }), 429
    return render_template("429.html", message=e.description), 429


# ==========================================
# CART HELPERS
# ==========================================
def get_cart():
    if "cart" not in session:
        session["cart"] = []
    return session["cart"]


def save_cart(cart):
    session["cart"] = cart
    session.modified = True


# ==========================================
# FRONT LOGIN GUARD
# ==========================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "users" not in session:
            flash("Please log in to access this page", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


# ==========================================
# CONTEXT PROCESSORS
# ==========================================
@app.context_processor
def utility_processor():
    def cart_count():
        cart = get_cart()
        return sum(item["quantity"] for item in cart)

    def is_logged_in():
        return "users" in session

    def current_user():
        return session.get("users", {})

    def get_brands():
        try:
            cats = Category.query.order_by(Category.name.asc()).all()
            if cats:
                return [c.name for c in cats]
        except Exception:
            pass
        return []

    def get_categories():
        try:
            return Category.query.order_by(Category.name.asc()).all()
        except Exception:
            return []

    return dict(
        cart_count=cart_count,
        is_logged_in=is_logged_in,
        current_user=current_user,
        get_brands=get_brands,
        get_categories=get_categories,
        get_image_url=get_image_url
    )


# ==========================================
# FRONT STORE ROUTES (CONNECTED TO DATABASE)
# ==========================================
@app.route("/")
@app.route("/index")
def index():
    categories = Category.query.order_by(Category.name.asc()).all()
    all_products = Product.query.order_by(Product.id.desc()).all()
    featured_products = all_products[:8]
    new_products = all_products[:8]
    brands = [c.name for c in categories]

    return render_template(
        "front/index.html",
        featured_products=featured_products,
        new_products=new_products,
        all_products=all_products,
        brands=brands,
        categories=categories
    )


@app.route("/shop")
def shop():
    brand = request.args.get("brand", "").strip()
    category_id = request.args.get("category_id", type=int)
    search = request.args.get("search", "").strip()
    sort = request.args.get("sort", "default")

    query = Product.query

    if category_id:
        query = query.filter(Product.category_id == category_id)
    elif brand and brand.lower() != "all":
        cat = Category.query.filter(Category.name.ilike(brand)).first()
        if cat:
            query = query.filter(Product.category_id == cat.id)

    if search:
        query = query.filter(
            (Product.name.ilike(f"%{search}%")) |
            (Product.description.ilike(f"%{search}%"))
        )

    if sort == "price_low":
        query = query.order_by(Product.price.asc())
    elif sort == "price_high":
        query = query.order_by(Product.price.desc())
    elif sort == "newest":
        query = query.order_by(Product.id.desc())
    elif sort == "name":
        query = query.order_by(Product.name.asc())
    else:
        query = query.order_by(Product.id.desc())

    products = query.all()
    categories = Category.query.order_by(Category.name.asc()).all()
    brands = [c.name for c in categories]

    return render_template(
        "front/shop.html",
        products=products,
        brands=brands,
        categories=categories,
        selected_brand=brand,
        selected_category=category_id,
        search_query=search,
        selected_sort=sort
    )


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        flash("Product not found", "error")
        return redirect(url_for("shop"))

    related = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id
    ).limit(4).all()

    return render_template(
        "front/product-detail.html",
        product=product,
        related=related
    )


@app.route("/add-to-cart", methods=["POST"])
@limiter.limit("60 per minute")
def add_to_cart():
    try:
        product_id = int(request.form.get("product_id"))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Invalid product ID"})

    quantity = max(1, int(request.form.get("quantity", 1)))
    color = request.form.get("color", "")
    storage = request.form.get("storage", "")
    buy_now = request.form.get("buy_now") == "1"

    product = db.session.get(Product, product_id)

    if not product:
        return jsonify({"success": False, "message": "Product not found"})

    if product.stock <= 0:
        return jsonify({"success": False, "message": "Sorry, this product is currently out of stock!"})

    cart = get_cart()

    # If buy now, unselect other items so this product is checked out exclusively
    if buy_now:
        for item in cart:
            item["selected"] = False

    for item in cart:
        if item["product_id"] == product_id and item.get("color") == color and item.get("storage") == storage:
            if item["quantity"] + quantity > product.stock:
                return jsonify({"success": False, "message": f"Only {product.stock} units available in stock!"})
            item["quantity"] += quantity
            item["selected"] = True
            save_cart(cart)
            return jsonify({
                "success": True,
                "cart_count": sum(i["quantity"] for i in cart),
                "message": f"Updated quantity for {product.name}"
            })

    cart.append({
        "product_id": product_id,
        "name": product.name,
        "price": float(product.price),
        "image": product.image,
        "quantity": quantity,
        "color": color,
        "storage": storage,
        "selected": True
    })
    save_cart(cart)

    return jsonify({
        "success": True,
        "cart_count": sum(i["quantity"] for i in cart),
        "message": f"{product.name} added to cart"
    })


@app.route("/cart")
@login_required
def cart():
    cart_items = get_cart()
    for item in cart_items:
        if "selected" not in item:
            item["selected"] = True

    selected_items = [item for item in cart_items if item.get("selected", True)]
    selected_count = len(selected_items)
    subtotal = sum(item["price"] * item["quantity"] for item in selected_items)
    shipping = 0 if subtotal > 500 else (0 if subtotal == 0 else 15)
    tax = round(subtotal * 0.1, 2)
    total = round(subtotal + shipping + tax, 2)

    return render_template(
        "front/cart.html",
        cart=cart_items,
        selected_count=selected_count,
        subtotal=subtotal,
        shipping=shipping,
        tax=tax,
        total=total
    )


@app.route("/cart/select", methods=["POST"])
@login_required
@limiter.limit("60 per minute")
def select_cart_items():
    data = request.get_json(silent=True) or request.form.to_dict()
    selected_indices = data.get("selected_indices", [])
    cart_items = get_cart()

    try:
        sel_set = set(int(i) for i in selected_indices)
    except (ValueError, TypeError):
        sel_set = set()

    for idx, item in enumerate(cart_items):
        item["selected"] = (idx in sel_set)

    save_cart(cart_items)

    selected_items = [item for item in cart_items if item.get("selected", True)]
    selected_count = len(selected_items)
    subtotal = sum(item["price"] * item["quantity"] for item in selected_items)
    shipping = 0 if subtotal > 500 else (0 if subtotal == 0 else 15)
    tax = round(subtotal * 0.1, 2)
    total = round(subtotal + shipping + tax, 2)

    return jsonify({
        "success": True,
        "selected_count": selected_count,
        "subtotal": subtotal,
        "shipping": shipping,
        "tax": tax,
        "total": total
    })


@app.route("/cart/select-all", methods=["POST"])
@login_required
@limiter.limit("60 per minute")
def select_all_cart_items():
    data = request.get_json(silent=True) or request.form.to_dict()
    select_all = data.get("select_all", True)
    if isinstance(select_all, str):
        select_all = select_all.lower() in ("true", "1")

    cart_items = get_cart()
    for item in cart_items:
        item["selected"] = bool(select_all)

    save_cart(cart_items)

    selected_items = [item for item in cart_items if item.get("selected", True)]
    selected_count = len(selected_items)
    subtotal = sum(item["price"] * item["quantity"] for item in selected_items)
    shipping = 0 if subtotal > 500 else (0 if subtotal == 0 else 15)
    tax = round(subtotal * 0.1, 2)
    total = round(subtotal + shipping + tax, 2)

    return jsonify({
        "success": True,
        "selected_count": selected_count,
        "subtotal": subtotal,
        "shipping": shipping,
        "tax": tax,
        "total": total
    })


@app.route("/order-confirmation")
@login_required
def order_confirmation():
    order = session.get("last_order")
    if not order:
        return redirect(url_for("index"))

    return render_template(
        "front/order-confirmation.html",
        order=order,
        order_id=order.get("order_id")
    )


@app.route("/update-cart", methods=["POST"])
@limiter.limit("60 per minute")
def update_cart():
    data = request.get_json(silent=True) or request.form.to_dict()
    cart_items = get_cart()
    action = data.get("action")
    index = data.get("index")
    selected_indices = data.get("selected_indices")

    if selected_indices is not None and isinstance(selected_indices, list):
        try:
            sel_set = set(int(i) for i in selected_indices)
            for idx, itm in enumerate(cart_items):
                itm["selected"] = (idx in sel_set)
        except (ValueError, TypeError):
            pass

    if index is not None:
        try:
            index = int(index)
            if 0 <= index < len(cart_items):
                if action == "increase":
                    cart_items[index]["quantity"] += 1
                elif action == "decrease":
                    if cart_items[index]["quantity"] > 1:
                        cart_items[index]["quantity"] -= 1
                    else:
                        cart_items.pop(index)
                elif action == "remove":
                    cart_items.pop(index)
        except ValueError:
            pass

    save_cart(cart_items)

    selected_items = [item for item in cart_items if item.get("selected", True)]
    selected_count = len(selected_items)
    subtotal = sum(item["price"] * item["quantity"] for item in selected_items)
    shipping = 0 if subtotal > 500 else (0 if subtotal == 0 else 15)
    tax = round(subtotal * 0.1, 2)
    total = round(subtotal + shipping + tax, 2)

    return jsonify({
        "success": True,
        "selected_count": selected_count,
        "subtotal": subtotal,
        "shipping": shipping,
        "tax": tax,
        "total": total
    })


@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    cart_items = get_cart()
    if not cart_items:
        flash("Your cart is empty", "warning")
        return redirect(url_for("shop"))

    if request.method == "POST":
        selected_indices = request.form.getlist("selected_items")
        if not selected_indices:
            data = request.get_json(silent=True) or {}
            selected_indices = data.get("selected_indices", [])
        if selected_indices:
            try:
                sel_set = set(int(i) for i in selected_indices)
                for idx, itm in enumerate(cart_items):
                    itm["selected"] = (idx in sel_set)
                save_cart(cart_items)
            except (ValueError, TypeError):
                pass

    selected_items = [item for item in cart_items if item.get("selected", True)]
    if not selected_items:
        flash("Please select at least 1 product from your cart to checkout.", "warning")
        return redirect(url_for("cart"))

    subtotal = sum(item["price"] * item["quantity"] for item in selected_items)
    shipping = 0 if subtotal > 500 else (0 if subtotal == 0 else 15)
    tax = round(subtotal * 0.1, 2)
    total = round(subtotal + shipping + tax, 2)

    return render_template(
        "front/checkout.html",
        items=selected_items,
        subtotal=subtotal,
        shipping=shipping,
        tax=tax,
        total=total
    )


@app.route("/place-order", methods=["POST"])
@login_required
@limiter.limit("10 per minute")
def place_order():
    try:
        fullname = request.form.get("fullname", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()
        city = request.form.get("city", "").strip()
        payment_method = request.form.get("payment", "Cash on Delivery")

        if not all([fullname, email, phone, address, city]):
            flash("Please fill in all required fields", "danger")
            return redirect(url_for("checkout"))

        cart_items = get_cart()
        if not cart_items:
            flash("Cart is empty", "warning")
            return redirect(url_for("cart"))

        selected_items = [item for item in cart_items if item.get("selected", True)]
        if not selected_items:
            flash("Please select at least 1 product to checkout.", "warning")
            return redirect(url_for("cart"))

        order_id = "ORD-" + str(uuid.uuid4())[:8].upper()
        subtotal = sum(item["price"] * item["quantity"] for item in selected_items)
        shipping = 0 if subtotal > 500 else (0 if subtotal == 0 else 15)
        tax = round(subtotal * 0.1, 2)
        total = round(subtotal + shipping + tax, 2)

        order_data = {
            "order_id": order_id,
            "order_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "customer_name": fullname,
            "customer_email": email,
            "customer_phone": phone,
            "shipping_address": address,
            "city": city,
            "payment_method": payment_method,
            "items": list(selected_items),
            "subtotal": subtotal,
            "shipping": shipping,
            "tax": tax,
            "total": total,
            "status": "Pending"
        }

        # Decrement stock in database for selected items only
        for item in selected_items:
            prod_id = item.get("product_id")
            if prod_id:
                p = db.session.get(Product, prod_id)
                if p:
                    p.stock = max(0, p.stock - item.get("quantity", 1))

        # Save order into database
        try:
            db_order = Order(
                order_id=order_id,
                customer_name=fullname,
                customer_email=email,
                customer_phone=phone,
                shipping_address=address,
                city=city,
                payment_method=payment_method,
                payment_status="Paid" if payment_method.lower() in ("card", "credit card", "stripe") else "Pending",
                status="Pending",
                subtotal=subtotal,
                shipping=shipping,
                tax=tax,
                total=total,
                items=list(selected_items)
            )
            db.session.add(db_order)
            db.session.commit()
        except Exception as db_err:
            print("DB order save notice:", db_err)
            db.session.commit()

        user_email = session["users"]["email"]
        if user_email not in USERS:
            USERS[user_email] = {
                "email": user_email,
                "name": session["users"].get("name", fullname),
                "orders": []
            }
        if "orders" not in USERS[user_email]:
            USERS[user_email]["orders"] = []

        USERS[user_email]["orders"].append(order_data)
        session["last_order"] = order_data

        # Send product photos via telegram if available for selected items
        for item in selected_items:
            image_url = item.get("image")
            caption = f"{item['name']}"
            if image_url:
                send_product_photo(image_url, caption)

        products_text = ""
        for item in selected_items:
            products_text += f"""
        📦 <b>Phone:</b> {item['name']}
        🔢 <b>Qty:</b> {item['quantity']}
        💲 <b>Price:</b> ${item['price']:.2f}
        """

        telegram_message = f"""
        🛒 <b>NEW ORDER</b>
        ━━━━━━━━━━━━━━
        🆔 <b>Order ID:</b> {order_id}
        👤 <b>Full Name:</b> {fullname}
        📧 <b>Email:</b> {email}
        📞 <b>Phone Number:</b> {phone}
        🏠 <b>Address:</b> {address}
        🏙️ <b>City:</b> {city}
        💳 <b>Payment:</b> {payment_method.upper()}
        ━━━━━━━━━━━━━━
        <b>PRODUCTS</b>
        {products_text}
        ━━━━━━━━━━━━━━
        💰 <b>Subtotal:</b> ${subtotal:.2f}
        🚚 <b>Shipping:</b> ${shipping:.2f}
        🧾 <b>Tax:</b> ${tax:.2f}
        ━━━━━━━━━━━━━━
        💵 <b>TOTAL:</b> ${total:.2f}
        """
        send_telegram_message(telegram_message)

        # Remove ONLY the selected items from the cart, keeping unselected items in cart
        remaining_cart = [item for item in cart_items if not item.get("selected", True)]
        for item in remaining_cart:
            item["selected"] = True
        save_cart(remaining_cart)

        flash(f"Order {order_id} placed successfully!", "success")
        return redirect(url_for("order_confirmation"))

    except Exception as e:
        print("Place order error:", e)
        flash("Order failed. Please try again.", "danger")
        return redirect(url_for("checkout"))


@app.route("/my-orders")
@login_required
def my_orders():
    user_email = session.get("users", {}).get("email")
    if not user_email:
        return redirect(url_for("login"))

    # Load persistent orders from DB
    orders = []
    try:
        db_orders = Order.query.filter_by(customer_email=user_email).order_by(Order.id.desc()).all()
        orders = [o.to_dict() for o in db_orders]
    except Exception:
        orders = []

    # Merge any in-memory orders if not in DB yet
    user_data = USERS.get(user_email, {})
    mem_orders = user_data.get("orders", [])
    existing_ids = {o.get("order_id") for o in orders}
    for mo in mem_orders:
        if isinstance(mo, dict) and mo.get("order_id") not in existing_ids:
            orders.append(mo)
            existing_ids.add(mo.get("order_id"))

    for order in orders:
        if not isinstance(order, dict):
            continue
        if "items" not in order or not isinstance(order["items"], list):
            order["items"] = []
        order.setdefault("status", "pending")
        order.setdefault("total", 0)
        order.setdefault("order_date", "N/A")
        order.setdefault("shipping_address", "")
        order.setdefault("city", "")
        order.setdefault("payment_method", "cash")

    return render_template("front/my-orders.html", orders=orders)


@app.route("/order/<order_id>")
@login_required
def order_detail(order_id):
    user_email = session["users"]["email"]
    order = None

    try:
        db_order = Order.query.filter_by(order_id=order_id).first()
        if db_order and (db_order.customer_email == user_email or session.get("user_role") == "admin"):
            order = db_order.to_dict()
    except Exception:
        order = None

    if not order:
        user_data = USERS.get(user_email, {})
        orders = user_data.get("orders", [])
        order = next((o for o in orders if o.get("order_id") == order_id), None)
        if not order:
            last_order = session.get("last_order")
            if last_order and last_order.get("order_id") == order_id:
                order = last_order

    if not order:
        flash("Order not found", "error")
        return redirect(url_for("my_orders"))

    return render_template("front/order-detail.html", order=order)


# ==========================================
# FRONT USER AUTHENTICATION
# ==========================================
@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute; 25 per hour")
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        # 1. Check database User model
        db_user = User.query.filter_by(email=email).first()
        if db_user and check_password_hash(db_user.password, password):
            session["users"] = {
                "id": db_user.id,
                "email": db_user.email,
                "name": db_user.name,
                "role": db_user.role
            }
            if db_user.role == "admin":
                session["user_id"] = db_user.id
                session["user_name"] = db_user.name
                session["user_email"] = db_user.email
                session["user_role"] = db_user.role
                session["logged_in"] = True

            flash("Login successful!", "success")
            return redirect(url_for("index"))

        # 2. Check USERS memory store
        user = USERS.get(email)
        if user and user.get("password") == password:
            session["users"] = {
                "email": user["email"],
                "name": user["name"],
                "role": user.get("role", "user")
            }
            flash("Login successful!", "success")
            return redirect(url_for("index"))

        flash("Invalid email or password", "error")

    return render_template("front/login.html")


@app.route("/logout")
def logout():
    session.pop("users", None)
    flash("You have been logged out", "info")
    return redirect(url_for("index"))


@app.route("/create-user", methods=["GET", "POST"])
@limiter.limit("5 per minute; 20 per hour")
def create_user():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash("All fields are required", "error")
            return render_template("front/create-user.html")

        if password != confirm_password:
            flash("Passwords do not match", "error")
            return render_template("front/create-user.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters", "error")
            return render_template("front/create-user.html")

        if email in USERS or User.query.filter_by(email=email).first():
            flash("Email already registered. Please login instead.", "error")
            return render_template("front/create-user.html")

        # Save to database
        hashed_password = generate_password_hash(password)
        new_user = User(
            name=name,
            email=email,
            password=hashed_password,
            role="user"
        )
        db.session.add(new_user)
        db.session.commit()

        # Save to memory store
        USERS[email] = {
            "email": email,
            "password": password,
            "name": name,
            "created_at": datetime.now().strftime("%Y-%m-%d"),
            "orders": []
        }

        # Auto-login after registration
        session["users"] = {
            "id": new_user.id,
            "email": email,
            "name": name,
            "role": "user"
        }

        flash(f"Account created successfully! Welcome, {name}!", "success")
        return redirect(url_for("index"))

    return render_template("front/create-user.html")


@app.route("/forget-pw", methods=["GET", "POST"])
@limiter.limit("3 per minute; 10 per hour")
def forget_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()

        db_user = User.query.filter_by(email=email).first()
        if email in USERS or db_user:
            flash(f"Password reset link has been sent to {email}", "success")
        else:
            flash("No account found with that email address", "error")

    return render_template("front/forget-pw.html")


@app.route("/profile")
@login_required
def profile():
    user = session.get("users", {})
    user_data = USERS.get(user.get("email"), user)
    return render_template("front/profile.html", user=user_data)


# ==========================================
# ADMIN STORE REDIRECTS (FOR SEAMLESS NAVIGATION)
# ==========================================
@app.route("/admin/product")
@app.route("/admin/products")
@admin_required
def admin_product_redirect():
    return redirect(url_for("admin.admin_products"))


@app.route("/admin/Phone")
@app.route("/admin/category")
@app.route("/admin/categories")
@admin_required
def admin_category_redirect():
    return redirect(url_for("admin.admin_categories"))


# Legacy aliases
admin_product = admin_product_redirect
admin_category = admin_category_redirect
admin_Phone = admin_category_redirect


@app.route("/admin/orders")
@admin_required
def admin_orders():
    return redirect(url_for("admin.admin_orders"))


# ==========================================
# UPLOADS & STATIC SERVING
# ==========================================
@app.route("/uploads/<folder>/<path:filename>")
def uploaded_file(folder, filename):
    safe_folder = os.path.basename(folder)
    folder_path = os.path.join(app.root_path, "static", "uploads", safe_folder)
    if not os.path.exists(folder_path):
        folder_path = os.path.join(app.root_path, "uploads", safe_folder)
    return send_from_directory(folder_path, os.path.basename(filename))


@app.route("/uploads/users/<path:filename>")
def user_image(filename):
    return uploaded_file("users", filename)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
