"""WSGI entry point for production servers (e.g. gunicorn run:app)."""
from app import create_app

app = create_app()
