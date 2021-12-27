import os
import tempfile
from pathlib import Path
import pytest

from forecast_app import create_app
from forecast_app.commands import init_db
from flask_sqlalchemy import SQLAlchemy


@pytest.fixture
def app():
    return create_app("test")


@pytest.fixture
def db(app):
    db = SQLAlchemy(app)
    with app.app_context():
        init_db()
        yield db
    os.unlink("forecast_app/" + app.config["SQLALCHEMY_DATABASE_URI"].split("///")[1])


@pytest.fixture
def client(app, db):
    with app.test_client() as client:
        yield client


def pytest_configure():
    pytest.FIXTURE_DIR = Path(__file__).parent / "fixtures"


class AuthActions:
    def __init__(self, client):
        self._client = client

    def login(self, username="admin", password="admin"):
        return self._client.post("/", data={"username": username, "password": password})

    def logout(self):
        return self._client.get("/logout")


@pytest.fixture
def auth(client):
    return AuthActions(client)
