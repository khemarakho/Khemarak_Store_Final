from flask import render_template, redirect, url_for
from . import admin_bp
from .auth import admin_required

# ==========================================
# ADMIN STORE & INVENTORY LEGACY ALIASES
# ==========================================

@admin_bp.route("/Phone")
@admin_required
def admin_Phone():
    return redirect(url_for("admin.admin_categories"))


@admin_bp.route("/Phone/all")
@admin_required
def admin_Phone_all():
    return redirect(url_for("admin.admin_products"))


@admin_bp.route("/Phone/Add")
@admin_required
def admin_Phone_Add():
    return redirect(url_for("admin.admin_product_add"))


@admin_bp.route("/Phone/brand")
@admin_required
def admin_Phone_brand():
    return redirect(url_for("admin.admin_categories"))
