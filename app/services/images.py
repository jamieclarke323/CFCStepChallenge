"""Secure handling of team logo uploads: validate, resize/crop, save."""
import os
import uuid

from flask import current_app
from PIL import Image, UnidentifiedImageError
from werkzeug.utils import secure_filename


class InvalidImageError(Exception):
    pass


def _allowed_extension(filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]


def save_team_image(file_storage, old_filename=None):
    """Validate, square-crop and resize an uploaded team image. Returns the new filename.

    Raises InvalidImageError on anything that looks unsafe or isn't a real image.
    """
    if not file_storage or not file_storage.filename:
        raise InvalidImageError("No file was selected.")

    if not _allowed_extension(file_storage.filename):
        raise InvalidImageError("Unsupported file type. Use PNG, JPG, GIF or WEBP.")

    try:
        image = Image.open(file_storage.stream)
        image.verify()  # confirms this is really an image, not a disguised file
    except (UnidentifiedImageError, OSError):
        raise InvalidImageError("That file doesn't look like a valid image.")

    # Re-open after verify() (which leaves the file unusable for further ops).
    file_storage.stream.seek(0)
    image = Image.open(file_storage.stream)
    image = image.convert("RGB")

    # Centre-crop to a square, then resize to the configured display size.
    width, height = image.size
    side = min(width, height)
    left = (width - side) // 2
    top = (height - side) // 2
    image = image.crop((left, top, left + side, top + side))
    image = image.resize(current_app.config["TEAM_IMAGE_SIZE"], Image.LANCZOS)

    safe_name = secure_filename(file_storage.filename)
    ext = safe_name.rsplit(".", 1)[-1].lower()
    if ext not in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        ext = "jpg"
    new_filename = f"{uuid.uuid4().hex}.jpg"
    dest_path = os.path.join(current_app.config["UPLOAD_FOLDER"], new_filename)
    image.save(dest_path, format="JPEG", quality=88)

    if old_filename:
        old_path = os.path.join(current_app.config["UPLOAD_FOLDER"], old_filename)
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except OSError:
                pass

    return new_filename
