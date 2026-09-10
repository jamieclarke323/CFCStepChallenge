"""Shared pytest fixtures for the test suite."""
import pytest

from app import create_app
from app.config import Config
from app.extensions import db
from app.models import User

TEST_PASSWORD = "correct horse battery staple"


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    CHALLENGE_START_DATE = None
    CHALLENGE_END_DATE = None
    RATELIMIT_ENABLED = False


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def make_user(first_name="Test", last_name="User", email="test@example.com", date_joined=None):
    user = User(first_name=first_name, last_name=last_name, email=email)
    user.set_password(TEST_PASSWORD)
    if date_joined is not None:
        user.date_joined = date_joined
    db.session.add(user)
    db.session.commit()
    return user
