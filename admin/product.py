import os
from decimal import Decimal
from flask import render_template, request, redirect, url_for, flash, current_app
from extensions import db, limiter
from models.category import Category
from models.product import Product
from models.product_image import ProductImage
from . import admin_bp
from .auth import admin_required
from upload_service import save_image_file, delete_image_file, get_image_url

# ==========================================
# LIST PRODUCTS
# ==========================================
@admin_bp.route("/products")
@admin_bp.route("/product")
@admin_required
def admin_products():
    search = request.args.get("search", "").strip()
    category_id = request.args.get("category_id", type=int)

    query = Product.query

    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))

    if category_id:
        query = query.filter(Product.category_id == category_id)

    products = query.order_by(Product.id.desc()).all()
    categories = Category.query.order_by(Category.name.asc()).all()

    total_products = len(products)
    out_of_stock = sum(1 for p in products if p.stock <= 0)
    total_stock = sum(p.stock for p in products)

    return render_template(
        "admin/product/products.html",
        module="products",
        products=products,
        categories=categories,
        search=search,
        selected_category=category_id,
        total_products=total_products,
        out_of_stock=out_of_stock,
        total_stock=total_stock,
        get_image_url=get_image_url
    )


# ==========================================
# ADD PRODUCT
# ==========================================
@admin_bp.route("/product/add", methods=["GET", "POST"])
@admin_bp.route("/product/create", methods=["GET", "POST"])
@admin_required
@limiter.limit("30 per minute")
def admin_product_add():
    categories = Category.query.order_by(Category.name.asc()).all()

    if not categories and request.method == "GET":
        flash("Please create at least one category before adding products!", "warning")
        return redirect(url_for("admin.admin_category_add"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category_id = request.form.get("category_id", type=int)
        cost_raw = request.form.get("cost", "0").strip()
        price_raw = request.form.get("price", "0").strip()
        stock_raw = request.form.get("stock", "0").strip()
        description = request.form.get("description", "").strip()

        # Validation
        if not name:
            flash("Product name is required!", "warning")
            return redirect(url_for("admin.admin_product_add"))

        if not category_id:
            flash("Category selection is required!", "warning")
            return redirect(url_for("admin.admin_product_add"))

        try:
            cost = Decimal(cost_raw) if cost_raw else Decimal("0.00")
            price = Decimal(price_raw)
            if price <= 0:
                raise ValueError
        except (ValueError, TypeError):
            flash("Please enter a valid positive price!", "warning")
            return redirect(url_for("admin.admin_product_add"))

        try:
            stock = max(0, int(stock_raw)) if stock_raw else 0
        except ValueError:
            stock = 0

        target_folder = current_app.config.get(
            "PRODUCT_UPLOAD_FOLDER",
            os.path.join(current_app.root_path, "static", "uploads", "products")
        )

        # Handle Thumbnail Upload Only
        thumbnail_file = request.files.get("thumbnail")
        thumbnail_filename = None

        if thumbnail_file and thumbnail_file.filename:
            thumbnail_filename = save_image_file(thumbnail_file, target_folder)

        # Create Product
        product = Product(
            name=name,
            thumbnail=thumbnail_filename,
            cost=cost,
            price=price,
            stock=stock,
            category_id=category_id,
            description=description if description else None
        )

        db.session.add(product)
        db.session.flush()  # Flush to generate product.id

        # Handle Multiple Additional Gallery Images (ProductImage)
        images = request.files.getlist("images")
        for img_file in images:
            if img_file and img_file.filename:
                img_name = save_image_file(img_file, target_folder)
                if img_name:
                    p_img = ProductImage(
                        product_id=product.id,
                        name=img_name
                    )
                    db.session.add(p_img)

        db.session.commit()
        flash(f"Product '{product.name}' created successfully!", "success")
        return redirect(url_for("admin.admin_products"))

    return render_template(
        "admin/product/add.html",
        module="products",
        categories=categories
    )


# ==========================================
# EDIT PRODUCT
# ==========================================
@admin_bp.route("/product/edit/<int:id>", methods=["GET", "POST"])
@admin_required
@limiter.limit("30 per minute")
def admin_product_edit(id):
    product = db.session.get(Product, id)
    if not product:
        flash("Product not found!", "danger")
        return redirect(url_for("admin.admin_products"))

    categories = Category.query.order_by(Category.name.asc()).all()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category_id = request.form.get("category_id", type=int)
        cost_raw = request.form.get("cost", "0").strip()
        price_raw = request.form.get("price", "0").strip()
        stock_raw = request.form.get("stock", "0").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Product name is required!", "warning")
            return redirect(url_for("admin.admin_product_edit", id=id))

        if not category_id:
            flash("Category selection is required!", "warning")
            return redirect(url_for("admin.admin_product_edit", id=id))

        try:
            cost = Decimal(cost_raw) if cost_raw else Decimal("0.00")
            price = Decimal(price_raw)
            if price <= 0:
                raise ValueError
        except (ValueError, TypeError):
            flash("Please enter a valid positive price!", "warning")
            return redirect(url_for("admin.admin_product_edit", id=id))

        try:
            stock = max(0, int(stock_raw)) if stock_raw else 0
        except ValueError:
            stock = 0

        target_folder = current_app.config.get(
            "PRODUCT_UPLOAD_FOLDER",
            os.path.join(current_app.root_path, "static", "uploads", "products")
        )

        product.name = name
        product.category_id = category_id
        product.cost = cost
        product.price = price
        product.stock = stock
        product.description = description if description else None

        # Replace thumbnail if new file provided
        thumbnail_file = request.files.get("thumbnail")
        if thumbnail_file and thumbnail_file.filename:
            if product.thumbnail:
                delete_image_file(product.thumbnail, target_folder)
            product.thumbnail = save_image_file(thumbnail_file, target_folder)

        # Add more gallery images
        new_images = request.files.getlist("images")
        for img_file in new_images:
            if img_file and img_file.filename:
                img_name = save_image_file(img_file, target_folder)
                if img_name:
                    p_img = ProductImage(
                        product_id=product.id,
                        name=img_name
                    )
                    db.session.add(p_img)

        db.session.commit()
        flash(f"Product '{product.name}' updated successfully!", "success")
        return redirect(url_for("admin.admin_products"))

    return render_template(
        "admin/product/edit.html",
        module="products",
        product=product,
        categories=categories,
        get_image_url=get_image_url
    )


# ==========================================
# DELETE PRODUCT
# ==========================================
@admin_bp.post("/product/delete/<int:id>")
@admin_required
@limiter.limit("30 per minute")
def admin_product_delete(id):
    product = db.session.get(Product, id)
    if not product:
        flash("Product not found!", "danger")
        return redirect(url_for("admin.admin_products"))

    product_name = product.name
    target_folder = current_app.config.get(
        "PRODUCT_UPLOAD_FOLDER",
        os.path.join(current_app.root_path, "static", "uploads", "products")
    )

    # Delete thumbnail
    if product.thumbnail:
        delete_image_file(product.thumbnail, target_folder)

    # Delete gallery images
    for img in product.images:
        delete_image_file(img.name, target_folder)

    db.session.delete(product)
    db.session.commit()

    flash(f"Product '{product_name}' deleted successfully!", "success")
    return redirect(url_for("admin.admin_products"))


# ==========================================
# DELETE SINGLE GALLERY IMAGE
# ==========================================
@admin_bp.post("/product-image/delete/<int:image_id>")
@admin_required
def admin_product_image_delete(image_id):
    p_img = db.session.get(ProductImage, image_id)
    if not p_img:
        flash("Image not found!", "danger")
        return redirect(request.referrer or url_for("admin.admin_products"))

    product_id = p_img.product_id
    target_folder = current_app.config.get(
        "PRODUCT_UPLOAD_FOLDER",
        os.path.join(current_app.root_path, "static", "uploads", "products")
    )

    delete_image_file(p_img.name, target_folder)
    db.session.delete(p_img)
    db.session.commit()

    flash("Gallery image removed successfully!", "success")
    return redirect(url_for("admin.admin_product_edit", id=product_id))
