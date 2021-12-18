import os
import tempfile
from pathlib import Path
import pytest

from forecast_app import create_app
from forecast_app.commands import upload_demo_data
from forecast_app.db import init_db
from flask_sqlalchemy import SQLAlchemy


@pytest.fixture
def app():
    return create_app(
        test_config={"TESTING": True, "USERS": {"test": {"password": "test"}}}
    )


@pytest.fixture
def db(app):
    """Create a database for testing."""
    db_fd, db_path = tempfile.mkstemp()
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///%s" % db_path
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.app_context().push()
    db = SQLAlchemy(app)
    with app.app_context():
        init_db()
        yield db
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app, db):
    with app.test_client() as client:
        yield client


def pytest_configure():
    pytest.FIXTURE_DIR = Path(__file__).parent / "fixtures"


class AuthActions:
    def __init__(self, client):
        self._client = client

    def login(self, username="test", password="test"):
        return self._client.post("/", data={"username": username, "password": password})

    def logout(self):
        return self._client.get("/logout")


@pytest.fixture
def auth(client):
    return AuthActions(client)
