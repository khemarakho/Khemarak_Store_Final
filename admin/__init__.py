from flask import Blueprint, session

from models.user import User


# ==========================================
# ADMIN BLUEPRINT
# ==========================================

admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)


# ==========================================
# CURRENT LOGGED-IN USER
# ==========================================

@admin_bp.app_context_processor
def inject_current_user():

    current_user = None

    user_id = session.get("user_id")

    if user_id:

        current_user = User.query.get(user_id)

    return {
        "current_user": current_user
    }


# ==========================================
# IMPORT ROUTES
# ==========================================

from . import auth
from . import dashboard
from . import user