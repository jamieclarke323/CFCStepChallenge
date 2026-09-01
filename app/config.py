"""Application configuration loaded from environment variables."""
import os
from datetime import date, timedelta

from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(BASE_DIR, ".env"))


def _parse_date(value):
    if not value:
        return None
    return date.fromisoformat(value.strip())


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

    _default_db_path = os.path.join(BASE_DIR, "instance", "step_challenge.db")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or f"sqlite:///{_default_db_path}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"timeout": 15}}

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "app", "static", "uploads", "teams")
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_MB", "5"))
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_UPLOAD_MB", "5")) * 1024 * 1024
    TEAM_IMAGE_SIZE = (512, 512)

    CHALLENGE_NAME = os.environ.get("CHALLENGE_NAME", "Steptember")
    CHALLENGE_START_DATE = _parse_date(os.environ.get("CHALLENGE_START_DATE"))
    CHALLENGE_END_DATE = _parse_date(os.environ.get("CHALLENGE_END_DATE"))
    MAX_PLAUSIBLE_DAILY_STEPS = int(os.environ.get("MAX_PLAUSIBLE_DAILY_STEPS", "100000"))

    REMEMBER_COOKIE_DAYS = int(os.environ.get("REMEMBER_COOKIE_DAYS", "35"))
    REMEMBER_COOKIE_DURATION = timedelta(days=REMEMBER_COOKIE_DAYS)
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"

    PERMANENT_SESSION_LIFETIME = timedelta(days=REMEMBER_COOKIE_DAYS)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Secure cookies require HTTPS; enable automatically outside local dev.
    SESSION_COOKIE_SECURE = os.environ.get("FLASK_ENV") == "production"
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE

    WTF_CSRF_TIME_LIMIT = None
