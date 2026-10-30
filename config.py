import os
from datetime import timedelta

class config:
    # ==========================================
    # Database & Security
    # ==========================================
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///app.db"
    SECRET_KEY = os.environ.get("SECRET_KEY", "mobile_shop_secret_key_2024_secure_and_unique")
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=1440)

    # ==========================================
    # CSRF Protection
    # ==========================================
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 86400  # 24 hours
    WTF_CSRF_CHECK_DEFAULT = True

    # ==========================================
    # Rate Limiting
    # ==========================================
    RATELIMIT_DEFAULT = "500 per day; 100 per hour"
    RATELIMIT_STRATEGY = "fixed-window"
    RATELIMIT_STORAGE_URI = "memory://"

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

    CATEGORY_UPLOAD_FOLDER = os.path.join(
        UPLOAD_FOLDER,
        "categories"
    )

    PRODUCT_UPLOAD_FOLDER = os.path.join(
        UPLOAD_FOLDER,
        "products"
    )

    ALLOWED_EXTENSIONS = {
        "jpg",
        "jpeg",
        "png",
        "gif",
        "webp"
    }

    # Maximum upload size: 100 MB (supports uploading multiple high-res product photos)
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024