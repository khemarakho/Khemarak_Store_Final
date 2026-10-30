from functools import wraps
import os
from flask import (
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)
from werkzeug.security import check_password_hash
from models.user import User
from extensions import db, limiter
from . import admin_bp

# ==========================================
# AUTH GUARDS & DECORATORS
# ==========================================

def login_required(view):
    """Ensure user is logged in."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id") or not session.get("logged_in"):
            flash("Please log in first.", "warning")
            return redirect(url_for("admin.admin_login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    """Ensure user is logged in AND possesses the admin role."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id or not session.get("logged_in"):
            flash("Please log in as an administrator first.", "warning")
            return redirect(url_for("admin.admin_login", next=request.path))

        # Check session role
        if session.get("user_role") != "admin":
            flash("Access denied: Administrator privileges required.", "danger")
            return redirect(url_for("admin.admin_login"))

        # Verify active user in database to ensure role is current
        user = db.session.get(User, user_id)
        if not user or user.role != "admin":
            session.clear()
            flash("Access denied: Invalid or deactivated administrator account.", "danger")
            return redirect(url_for("admin.admin_login"))

        return view(*args, **kwargs)
    return wrapped


# ==========================================
# ADMIN LOGIN
# ==========================================
@admin_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute; 20 per hour")
def admin_login():
    # ==========================================
    # GET
    # ==========================================
    if request.method == "GET":
        if session.get("logged_in") and session.get("user_role") == "admin":
            return redirect(url_for("admin.admin_dashboard"))
        return render_template("admin/login.html")

    # ==========================================
    # FORM DATA
    # ==========================================
    name = request.form.get("name", "").strip()
    password = request.form.get("password", "")

    # ==========================================
    # VALIDATION
    # ==========================================
    if not name or not password:
        flash("Please enter both name and password.", "warning")
        return redirect(url_for("admin.admin_login"))

    # ==========================================
    # FIND USER
    # ==========================================
    user = User.query.filter_by(name=name).first()

    # User not found
    if user is None:
        flash("Invalid name or password.", "danger")
        return redirect(url_for("admin.admin_login"))

    # Verify password
    if not user.password:
        flash("Invalid name or password.", "danger")
        return redirect(url_for("admin.admin_login"))

    try:
        password_correct = check_password_hash(user.password, password)
    except Exception as e:
        print("Password check error:", e)
        password_correct = False

    if not password_correct:
        flash("Invalid name or password.", "danger")
        return redirect(url_for("admin.admin_login"))

    # ==========================================
    # ADMIN ROLE CHECK
    # ==========================================
    if user.role != "admin":
        flash("Access denied: Administrator privileges required.", "danger")
        return redirect(url_for("admin.admin_login"))

    # ==========================================
    # LOGIN SUCCESS - INITIALIZE SESSION
    # ==========================================
    session.clear()
    session["user_id"] = user.id
    session["user_name"] = user.name
    session["user_email"] = user.email
    session["user_role"] = user.role

    # User profile image
    if user.image:
        image_name = os.path.basename(user.image.replace("\\", "/"))
        session["user_image"] = image_name
    else:
        session["user_image"] = None

    session["logged_in"] = True

    flash("Logged in successfully as Administrator!", "success")
    next_url = request.args.get("next")
    if next_url and next_url.startswith("/admin") and not next_url.startswith("/admin/login"):
        return redirect(next_url)

    return redirect(url_for("admin.admin_dashboard"))


# ==========================================
# ADMIN LOGOUT
# ==========================================
@admin_bp.route("/logout")
def admin_logout():
    session.clear()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for("admin.admin_login"))