import os
import uuid
from .auth import login_required
from flask import (render_template, request, redirect, url_for, flash, current_app)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from extensions import db
from models import User
from . import admin_bp
# =========================================================
# ALLOWED FILE
# =========================================================
def allowed_file(filename):
    if "." not in filename:
        return False
    extension = filename.rsplit(
        ".",
        1
    )[1].lower()
    return extension in current_app.config[
        "ALLOWED_EXTENSIONS"
    ]
# =========================================================
# SAVE USER IMAGE
# =========================================================
def save_user_image(image):
    if not image:
        return None
    if not image.filename:
        return None
    if not allowed_file(image.filename):
        return None
    filename = secure_filename(
        image.filename)
    upload_folder = current_app.config[
        "USER_UPLOAD_FOLDER"]
    os.makedirs(
        upload_folder,
        exist_ok=True)
    file_path = os.path.join(
        upload_folder,
        filename)
    # If aaa.png already exists,
    # create aaa_1.png, aaa_2.png, etc.
    if os.path.exists(file_path):
        name, extension = os.path.splitext(
            filename
        )
        counter = 1
        while True:
            new_filename = (
                f"{name}_{counter}{extension}"
            )
            new_path = os.path.join(
                upload_folder,
                new_filename
            )
            if not os.path.exists(new_path):
                filename = new_filename
                file_path = new_path
                break
            counter += 1
    image.save(file_path)
    return filename
# =========================================================
# DELETE USER IMAGE
# =========================================================
def delete_user_image(filename):
    if not filename:
        return
    file_path = os.path.join(
        current_app.config["USER_UPLOAD_FOLDER"],
        filename
    )

    if os.path.exists(file_path):

        try:
            os.remove(file_path)

        except OSError:
            pass
# =========================================================
# USERS LIST
# =========================================================

@admin_bp.get("/users")
@login_required
def admin_users():
    users = User.query.order_by(
        User.id.desc()
    ).all()
    return render_template(
        "admin/user/users.html",
        module="users",
        users=users
    )
# =========================================================
# ADD USER
# GET  -> Show form
# POST -> Create user
# =========================================================
@admin_bp.route(
    "/user/add",
    methods=["GET", "POST"]
)
@login_required
def add():
    if request.method == "POST":
        # -----------------------------------------
        # Get form data
        # ----------------------------------------

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        role = request.form.get(
            "role",
            "user"
        )

        # -----------------------------------------
        # Validate
        # -----------------------------------------

        if not name or not email or not password:
            flash(
                "All fields are required!",
                "danger"
            )

            return redirect(
                url_for("admin.add")
            )

        # -----------------------------------------
        # Check duplicate email
        # -----------------------------------------

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:
            flash(
                "Email already exists!",
                "danger"
            )

            return redirect(
                url_for("admin.add")
            )

        # -----------------------------------------
        # Upload image
        # -----------------------------------------

        image = request.files.get(
            "image"
        )

        filename = None

        if image and image.filename:

            filename = save_user_image(
                image
            )

            if filename is None:
                flash(
                    "Invalid image type!",
                    "danger"
                )

                return redirect(
                    url_for("admin.add")
                )

        # -----------------------------------------
        # Create user
        # -----------------------------------------

        user = User(

            image=filename,

            name=name,

            email=email,

            password=generate_password_hash(
                password
            ),

            role=role
        )

        db.session.add(user)

        db.session.commit()

        flash(
            "User added successfully!",
            "success"
        )

        return redirect(
            url_for("admin.admin_users")
        )

    # -----------------------------------------
    # GET
    # -----------------------------------------

    return render_template(
        "admin/user/add.html",
        module="add"
    )
# =========================================================
# EDIT USER - SHOW FORM
# =========================================================

@admin_bp.get(
    "/user/edit/<int:id>"
)
@login_required
def admin_user_edit(id):
    user = User.query.get_or_404(
        id
    )

    return render_template(
        "admin/user/edit.html",
        module="user",
        user=user
    )
# =========================================================
# EDIT USER - UPDATE
# =========================================================
@admin_bp.post("/user/edit")
@login_required
def edit():
    user_id = request.form.get(
        "user_id"
    )
    user = User.query.get_or_404(
        user_id
    )
    # -----------------------------------------
    # Basic information
    # -----------------------------------------

    name = request.form.get(
        "name",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip().lower()

    role = request.form.get(
        "role",
        "user"
    )

    if not name or not email:
        flash(
            "Name and email are required!",
            "danger"
        )

        return redirect(
            url_for(
                "admin.admin_user_edit",
                id=user.id
            )
        )

    # -----------------------------------------
    # Check duplicate email
    # -----------------------------------------

    existing_user = User.query.filter(
        User.email == email,
        User.id != user.id
    ).first()

    if existing_user:
        flash(
            "Email already exists!",
            "danger"
        )

        return redirect(
            url_for(
                "admin.admin_user_edit",
                id=user.id
            )
        )

    user.name = name

    user.email = email

    user.role = role

    # -----------------------------------------
    # Password
    # -----------------------------------------

    password = request.form.get(
        "password",
        ""
    )

    if password:
        user.password = generate_password_hash(
            password
        )

    # -----------------------------------------
    # New image
    # -----------------------------------------

    image = request.files.get(
        "image"
    )

    if image and image.filename:

        new_filename = save_user_image(
            image
        )

        if new_filename is None:
            flash(
                "Invalid image type!",
                "danger"
            )

            return redirect(
                url_for(
                    "admin.admin_user_edit",
                    id=user.id
                )
            )

        # Delete old image
        delete_user_image(
            user.image
        )

        # Save new filename
        user.image = new_filename

    # -----------------------------------------
    # Save
    # -----------------------------------------

    db.session.commit()

    flash(
        "User updated successfully!",
        "success"
    )

    return redirect(
        url_for("admin.admin_users")
    )


# =========================================================
# DELETE USER - CONFIRM PAGE
# =========================================================

@admin_bp.get(
    "/user/delete/<int:user_id>"
)
@login_required
def confirm_delete(user_id):
    user = User.query.get_or_404(
        user_id
    )

    return render_template(
        "admin/user/delete.html",
        module="user",
        user=user
    )


# =========================================================
# DELETE USER
# =========================================================

@admin_bp.post(
    "/user/delete"
)
@login_required
def delete_user():
    user_id = request.form.get(
        "user_id"
    )

    user = User.query.get_or_404(
        user_id
    )

    # -----------------------------------------
    # Delete image
    # -----------------------------------------

    delete_user_image(
        user.image
    )

    # -----------------------------------------
    # Delete user
    # -----------------------------------------

    db.session.delete(user)

    db.session.commit()

    flash(
        "User deleted successfully!",
        "success"
    )

    return redirect(
        url_for("admin.admin_users")
    )
