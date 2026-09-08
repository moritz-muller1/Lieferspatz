"""Cloudinary image uploads. Returns None when CLOUDINARY_URL is unset so
callers fall back to the bundled placeholder images."""
import cloudinary
import cloudinary.uploader
from flask import current_app


def _configured():
    return bool(current_app.config.get('CLOUDINARY_URL'))


def init_app(app):
    if app.config.get('CLOUDINARY_URL'):
        # cloudinary reads CLOUDINARY_URL from the environment itself.
        cloudinary.config(secure=True)


def upload_image(file_storage, public_id):
    if not file_storage or not getattr(file_storage, 'filename', ''):
        return None
    if not _configured():
        current_app.logger.warning('CLOUDINARY_URL not set - skipping image upload')
        return None
    result = cloudinary.uploader.upload(
        file_storage,
        public_id=public_id,
        folder='lieferspatz',
        overwrite=True,
        resource_type='image',
    )
    return result.get('secure_url')
