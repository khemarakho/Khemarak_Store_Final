import os
import uuid
from flask import current_app, url_for
from werkzeug.utils import secure_filename
from PIL import Image

DEFAULT_ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}


def allowed_file(filename, allowed_extensions=None):
    """Check if file extension is in allowed extensions."""
    if not allowed_extensions:
        allowed_extensions = (
            current_app.config.get("ALLOWED_EXTENSIONS")
            if current_app else DEFAULT_ALLOWED_EXTENSIONS
        )
    return (
        "." in filename and
        filename.rsplit(".", 1)[1].lower() in allowed_extensions
    )


# Alias for backward compatibility
is_allowed_file = allowed_file


def save_image_file(file, target_folder, allowed_extensions=None):
    """Save an uploaded image file securely with a unique filename."""
    if not file or not file.filename:
        return None

    if not allowed_file(file.filename, allowed_extensions):
        return None

    os.makedirs(target_folder, exist_ok=True)

    original_filename = secure_filename(file.filename)
    name, ext = os.path.splitext(original_filename)
    unique_filename = f"{uuid.uuid4().hex[:12]}_{name}{ext.lower()}"
    file_path = os.path.join(target_folder, unique_filename)

    file.save(file_path)
    return unique_filename


def delete_image_file(filename, target_folder):
    """Delete an image file from the target directory if it exists."""
    if not filename or filename.startswith("http://") or filename.startswith("https://"):
        return

    # Clean path traversal attempts
    safe_name = os.path.basename(filename)
    file_path = os.path.join(target_folder, safe_name)

    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError:
            pass


def get_image_url(image_name, folder_type="products"):
    """
    Return the proper web URL for an image name.
    Supports external URLs, static uploads, and fallback defaults.
    """
    if not image_name:
        if folder_type == "categories":
            return "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=600&auto=format&fit=crop&q=80"
        return "https://images.unsplash.com/photo-1592750475338-74b7b21085ab?w=600&auto=format&fit=crop&q=80"

    clean_str = str(image_name).strip()

    # Already an external URL
    if clean_str.startswith("http://") or clean_str.startswith("https://"):
        return clean_str

    # If it starts with /static/ or static/
    clean_name = clean_str.replace("\\", "/").lstrip("/")
    if clean_name.startswith("static/"):
        return "/" + clean_name

    if clean_name.startswith("uploads/"):
        return f"/static/{clean_name}"

    # Relative filename inside uploads/<folder_type>/
    safe_name = os.path.basename(clean_name)
    return f"/static/uploads/{folder_type}/{safe_name}"


def save_image(
    file,
    upload_folder,
    allowed_extensions=None,
    resize_to=(800, 800),
    thumb_size=(200, 200)
):
    """Save image with resized versions and thumbnails."""
    if not file or file.filename == "":
        return None

    if not allowed_file(file.filename, allowed_extensions):
        return None

    os.makedirs(upload_folder, exist_ok=True)

    filename = secure_filename(file.filename)
    _, ext = os.path.splitext(filename)
    unique_name = uuid.uuid4().hex

    original_filename = f"{unique_name}{ext}"
    resized_filename = f"{unique_name}_resized{ext}"
    thumb_filename = f"{unique_name}_thumb{ext}"

    original_path = os.path.join(upload_folder, original_filename)
    resized_path = os.path.join(upload_folder, resized_filename)
    thumb_path = os.path.join(upload_folder, thumb_filename)

    file.save(original_path)

    try:
        image = Image.open(original_path)
        resized = image.copy()
        resized.thumbnail(resize_to)
        resized.save(resized_path)

        thumb = image.copy()
        thumb.thumbnail(thumb_size)
        thumb.save(thumb_path)
    except Exception:
        pass

    return {
        "original": original_filename,
        "resized": resized_filename,
        "thumbnail": thumb_filename
    }