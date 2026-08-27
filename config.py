import os
from datetime import timedelta
class config:
    # ==========================================
    # Database
    # ==========================================
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///app.db"
    SECRET_KEY = "mobile_shop_secret_key_2024"
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=1440)

    # ==========================================
    # Base Directory
    # ==========================================

    BASE_DIR = os.path.dirname(
        os.path.abspath(__file__)
    )


    # ==========================================
    # Upload
    # ==========================================

    UPLOAD_FOLDER = os.path.join(
        BASE_DIR,
        "static",
        "uploads"
    )

    USER_UPLOAD_FOLDER = os.path.join(
        UPLOAD_FOLDER,
        "users"
    )

    ALLOWED_EXTENSIONS = {
        "jpg",
        "jpeg",
        "png",
        "gif",
        "webp"
    }

    # Maximum 10 MB
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024