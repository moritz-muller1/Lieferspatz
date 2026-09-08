"""Environment-driven configuration (loaded from .env locally)."""
import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-only-insecure-key')
    DATABASE_URL = os.environ.get('DATABASE_URL')
    CLOUDINARY_URL = os.environ.get('CLOUDINARY_URL')

    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024

    # Secure cookies need HTTPS: on in production (Render sets RENDER), off for
    # local http. Force with SESSION_COOKIE_SECURE=true/false.
    SESSION_COOKIE_SECURE = os.environ.get(
        'SESSION_COOKIE_SECURE',
        'true' if os.environ.get('RENDER') else 'false',
    ).lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
