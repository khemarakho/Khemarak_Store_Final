from flask import Blueprint, session, request, redirect, url_for, flash
from models.user import User
from extensions import db

# ==========================================
# ADMIN BLUEPRINT
# ==========================================

admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)

# ==========================================
# AUTH GUARD FOR ENTIRE ADMIN BLUEPRINT
# ==========================================
@admin_bp.before_request
def admin_auth_guard():
    endpoint = request.endpoint or ""
    # Allow admin login, admin logout, and static file endpoints
    if endpoint in ("admin.admin_login", "admin.admin_logout") or request.path.startswith("/admin/static"):
        return None

    user_id = session.get("user_id")
    if not user_id or not session.get("logged_in"):
        flash("Please log in to access the administrator panel.", "warning")
        return redirect(url_for("admin.admin_login", next=request.path))

    if session.get("user_role") != "admin":
        flash("Access denied: Administrator privileges required.", "danger")
        return redirect(url_for("admin.admin_login"))


# ==========================================
# CURRENT LOGGED-IN ADMIN CONTEXT
# ==========================================
@admin_bp.app_context_processor
def inject_current_user():
    current_user = None
    user_id = session.get("user_id")
    if user_id:
        current_user = db.session.get(User, user_id)
    return {
        "current_user": current_user
    }


# ==========================================
# IMPORT ROUTES
# ==========================================
from . import auth
from . import dashboard
from . import user
from . import category
from . import product
from . import order
from . import store_routes