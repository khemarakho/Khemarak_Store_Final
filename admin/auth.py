from functools import wraps
import os
from . import admin_bp
from flask import (
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash)
from werkzeug.security import check_password_hash
from models.user import User
# ==========================================
# LOGIN REQUIRED
# ==========================================
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash(
                "Please log in first.",
                "warning"
            )
            return redirect(
                url_for(
                    "admin.admin_login",
                    next=request.path
                )
            )
        return view(*args, **kwargs)
    return wrapped
# ==========================================
# ADMIN LOGIN
# ==========================================
@admin_bp.route(
    "/login",
    methods=["GET", "POST"])
def admin_login():
    # ==========================================
    # GET
    # ==========================================
    if request.method == "GET":

        if session.get("logged_in"):

            return redirect(
                url_for(
                    "admin.admin_dashboard"
                )
            )
        return render_template(
            "admin/login.html"
        )
    # ==========================================
    # FORM DATA
    # ==========================================
    name = request.form.get(
        "name",
        ""
    ).strip()
    password = request.form.get(
        "password",
        ""
    )
    # ==========================================
    # VALIDATION
    # ==========================================
    if not name or not password:
        flash(
            "Please enter name and password.",
            "warning"
        )
        return redirect(
            url_for(
                "admin.admin_login"
            )
        )
    # ==========================================
    # FIND USER
    # ==========================================
    user = User.query.filter_by(
        name=name
    ).first()
    # ==========================================
    # USER NOT FOUND
    # ==========================================
    if user is None:
        flash(
            "Invalid name or password.",
            "danger"
        )
        return redirect(
            url_for(
                "admin.admin_login"
            )
        )
    # ==========================================
    # DEBUG DATABASE
    # ==========================================

    print("================================")
    print("USER ID    :", user.id)
    print("USER NAME  :", user.name)
    print("USER EMAIL :", user.email)
    print("USER IMAGE :", repr(user.image))
    print("USER ROLE  :", user.role)
    print("================================")
    # ==========================================
    # CHECK PASSWORD
    # ==========================================
    if not user.password:
        flash(
            "Invalid name or password.",
            "danger"
        )
        return redirect(
            url_for(
                "admin.admin_login"
            )
        )
    try:

        password_correct = check_password_hash(
            user.password,
            password
        )

    except Exception as e:
        print(
            "Password error:",e)
        password_correct = False
    if not password_correct:
        flash(
            "Invalid name or password.",
            "danger"
        )

        return redirect(
            url_for(
                "admin.admin_login"
            )
        )
    # ==========================================
    # LOGIN SUCCESS
    # ==========================================
    session.clear()
    session["user_id"] = user.id
    session["user_name"] = user.name
    session["user_email"] = user.email
    session["user_role"] = user.role
    # ==========================================
    # USER IMAGE
    #
    # IMPORTANT:
    # Save ONLY filename
    #
    # Example:
    # admin.jpg
    #
    # NOT:
    # static/uploads/users/admin.jpg
    #
    # NOT:
    # uploads/users/admin.jpg
    # ==========================================
    if user.image:
        image_name = os.path.basename(
            user.image.replace(
                "\\",
                "/"
            ))
        session["user_image"] = image_name
    else:
        session["user_image"] = None
    # ==========================================
    # LOGGED IN
    # ==========================================
    session["logged_in"] = True
    # ==========================================
    # DEBUG SESSION
    # ==========================================
    print("================================")
    print("LOGIN SUCCESS")
    print("USER ID    :", session.get("user_id"))
    print("USER NAME  :", session.get("user_name"))
    print("USER EMAIL :", session.get("user_email"))
    print("USER ROLE  :", session.get("user_role"))
    print("USER IMAGE :", session.get("user_image"))
    print("================================")
    # ==========================================
    # SUCCESS
    # ==========================================
    flash(
        "Login successfully!",
        "success"
    )
    return redirect(
        url_for(
            "admin.admin_dashboard"
        )
    )
# ==========================================
# ADMIN LOGOUT
# ==========================================
@admin_bp.route(
    "/logout")
def admin_logout():
    session.clear()
    flash(
        "You have been logged out.",
        "success"
    )
    return redirect(
        url_for(
            "admin.admin_login"
        )
    )