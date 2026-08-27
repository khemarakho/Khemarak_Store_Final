import os
import uuid

from werkzeug.utils import secure_filename
from PIL import Image


def allowed_file(filename, allowed_extensions):
    return (
        '.' in filename and
        filename.rsplit('.', 1)[1].lower() in allowed_extensions
    )


def save_image(
    file,
    upload_folder,
    allowed_extensions,
    resize_to=(800, 800),
    thumb_size=(200, 200)
):
    if not file or file.filename == '':
        return None

    if not allowed_file(file.filename, allowed_extensions):
        return None

    # Create folder if it does not exist
    os.makedirs(upload_folder, exist_ok=True)

    filename = secure_filename(file.filename)

    # Get extension
    _, ext = os.path.splitext(filename)

    # Generate unique filename
    unique_name = uuid.uuid4().hex

    original_filename = f"{unique_name}{ext}"
    resized_filename = f"{unique_name}_resized{ext}"
    thumb_filename = f"{unique_name}_thumb{ext}"

    original_path = os.path.join(
        upload_folder,
        original_filename
    )

    resized_path = os.path.join(
        upload_folder,
        resized_filename
    )

    thumb_path = os.path.join(
        upload_folder,
        thumb_filename
    )

    # Save original
    file.save(original_path)

    # Open image
    image = Image.open(original_path)

    # Resize
    resized = image.copy()
    resized.thumbnail(resize_to)
    resized.save(resized_path)

    # Thumbnail
    thumb = image.copy()
    thumb.thumbnail(thumb_size)
    thumb.save(thumb_path)

    return {
        "original": original_filename,
        "resized": resized_filename,
        "thumbnail": thumb_filename
    }