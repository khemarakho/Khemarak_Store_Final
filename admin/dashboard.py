from . import admin_bp
from .auth import login_required
from flask import render_template,session,redirect,url_for
@admin_bp.get("/dashboard")
@login_required
def admin_dashboard():
    # ==========================================
    # DASHBOARD
    # ==========================================
    return render_template(
        "admin/dashboard/admin.html",
        module="admin")