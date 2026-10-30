import os
from flask import render_template, request, redirect, url_for, flash, current_app
from extensions import db, limiter
from models.category import Category
from . import admin_bp
from .auth import admin_required
from upload_service import save_image_file, delete_image_file, get_image_url

# ==========================================
# LIST CATEGORIES
# ==========================================
@admin_bp.route("/categories")
@admin_bp.route("/category")
@admin_required
def admin_categories():
    search = request.args.get("search", "").strip()
    query = Category.query

    if search:
        query = query.filter(Category.name.ilike(f"%{search}%"))

    categories = query.order_by(Category.id.desc()).all()

    return render_template(
        "admin/category/index.html",
        module="categories",
        categories=categories,
        search=search,
        get_image_url=get_image_url
    )


# ==========================================
# ADD CATEGORY
# ==========================================
@admin_bp.route("/category/add", methods=["GET", "POST"])
@admin_required
@limiter.limit("30 per minute")
def admin_category_add():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        image_file = request.files.get("image")

        if not name:
            flash("Category name is required!", "warning")
            return redirect(url_for("admin.admin_category_add"))

        # Check duplicate name
        existing = Category.query.filter_by(name=name).first()
        if existing:
            flash(f"A category named '{name}' already exists!", "warning")
            return redirect(url_for("admin.admin_category_add"))

        # Handle image upload only
        image_filename = None
        if image_file and image_file.filename:
            target_folder = current_app.config.get(
                "CATEGORY_UPLOAD_FOLDER",
                os.path.join(current_app.root_path, "static", "uploads", "categories")
            )
            image_filename = save_image_file(image_file, target_folder)

        category = Category(
            name=name,
            description=description if description else None,
            image=image_filename
        )

        db.session.add(category)
        db.session.commit()

        flash(f"Category '{category.name}' created successfully!", "success")
        return redirect(url_for("admin.admin_categories"))

    return render_template(
        "admin/category/add.html",
        module="categories"
    )


# ==========================================
# EDIT CATEGORY
# ==========================================
@admin_bp.route("/category/edit/<int:id>", methods=["GET", "POST"])
@admin_required
@limiter.limit("30 per minute")
def admin_category_edit(id):
    category = db.session.get(Category, id)
    if not category:
        flash("Category not found!", "danger")
        return redirect(url_for("admin.admin_categories"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        image_file = request.files.get("image")

        if not name:
            flash("Category name is required!", "warning")
            return redirect(url_for("admin.admin_category_edit", id=id))

        # Check duplicate name with other categories
        existing = Category.query.filter(Category.name == name, Category.id != id).first()
        if existing:
            flash(f"Another category named '{name}' already exists!", "warning")
            return redirect(url_for("admin.admin_category_edit", id=id))

        category.name = name
        category.description = description if description else None

        # Handle new image upload only
        if image_file and image_file.filename:
            target_folder = current_app.config.get(
                "CATEGORY_UPLOAD_FOLDER",
                os.path.join(current_app.root_path, "static", "uploads", "categories")
            )
            # Remove old file if it was local
            if category.image:
                delete_image_file(category.image, target_folder)
            category.image = save_image_file(image_file, target_folder)

        db.session.commit()
        flash(f"Category '{category.name}' updated successfully!", "success")
        return redirect(url_for("admin.admin_categories"))

    return render_template(
        "admin/category/edit.html",
        module="categories",
        category=category,
        get_image_url=get_image_url
    )


# ==========================================
# DELETE CATEGORY
# ==========================================
@admin_bp.post("/category/delete/<int:id>")
@admin_required
@limiter.limit("30 per minute")
def admin_category_delete(id):
    category = db.session.get(Category, id)
    if not category:
        flash("Category not found!", "danger")
        return redirect(url_for("admin.admin_categories"))

    category_name = category.name
    # Delete image file if exists
    if category.image:
        target_folder = current_app.config.get(
            "CATEGORY_UPLOAD_FOLDER",
            os.path.join(current_app.root_path, "static", "uploads", "categories")
        )
        delete_image_file(category.image, target_folder)

    db.session.delete(category)
    db.session.commit()

    flash(f"Category '{category_name}' and its products deleted successfully!", "success")
    return redirect(url_for("admin.admin_categories"))
