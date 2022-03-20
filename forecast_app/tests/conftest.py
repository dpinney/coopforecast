import os
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest
from flask_sqlalchemy import SQLAlchemy

from forecast_app import create_app
from forecast_app.commands import init_db, upload_demo_data
from forecast_app.config import TestingConfig

BACKUP_DB_PATH = "forecast_app/db/backup.db"


def load_demo_db(app):
    """Loading data via CSV is a lengthy process. Store a backup, and refresh when necessary."""
    test_path = db_path(app)
    if os.path.exists(BACKUP_DB_PATH):
        shutil.copyfile(BACKUP_DB_PATH, test_path)
    else:
        init_db()
        upload_demo_data()
        shutil.copyfile(test_path, BACKUP_DB_PATH)


def db_path(app):
    return "forecast_app/" + app.config["SQLALCHEMY_DATABASE_URI"].split("///")[1]


@pytest.fixture(scope="session", autouse=True)
def setup_and_cleanup(request):
    os.makedirs(TestingConfig.OUTPUT_DIR)
    os.makedirs(TestingConfig.UPLOAD_DIR)
    yield None
    shutil.rmtree(TestingConfig.OUTPUT_DIR)
    shutil.rmtree(TestingConfig.UPLOAD_DIR)
    if os.path.exists(BACKUP_DB_PATH):
        os.remove(BACKUP_DB_PATH)


@pytest.fixture
def app():
    return create_app("test")


@pytest.fixture
def db(app):
    db = SQLAlchemy(app)
    with app.app_context():
        init_db()
        yield db
    os.unlink(db_path(app))


@pytest.fixture
def client(app, db):
    with app.test_client() as client:
        yield client


# https://stackoverflow.com/questions/15753390/how-can-i-mock-requests-and-the-response
class MockResponse:
    def __init__(self, mock_path, status_code):
        self.status_code = status_code
        with open(mock_path, "r") as f:
            self.text = f.read()


def mocked_asos_response(*args, **kwargs):
    mock_path = pytest.FIXTURE_DIR / "asos-response.csv"
    return MockResponse(mock_path, 200)


def mocked_nws_response(*args, **kwargs):
    mock_path = pytest.FIXTURE_DIR / "nws-response.json"
    return MockResponse(mock_path, 200)


def pytest_configure():
    pytest.FIXTURE_DIR = Path(__file__).parent / "fixtures"
    pytest.load_demo_db = load_demo_db
    pytest.init_db = init_db
    pytest.asos_patch = patch("requests.get", side_effect=mocked_asos_response)
    pytest.nws_patch = patch("requests.get", side_effect=mocked_nws_response)


class AuthActions:
    def __init__(self, client):
        self._client = client

    def login(self):
        return self._client.post(
            "/",
            data={
                "username": TestingConfig.ADMIN_USER,
                "password": TestingConfig.ADMIN_PASSWORD,
            },
        )

    def logout(self):
        return self._client.get("/logout")


@pytest.fixture
def auth(client):
    return AuthActions(client)
