import os
import shutil
from pathlib import Path
import pytest

from forecast_app import create_app
from forecast_app.config import TestingConfig
from forecast_app.commands import init_db, upload_demo_data
from flask_sqlalchemy import SQLAlchemy


BACKUP_DB_PATH = "forecast_app/db/backup.db"


def load_demo_db(app):
    test_path = db_path(app)
    if os.path.exists(BACKUP_DB_PATH):
        os.system(f"cp {BACKUP_DB_PATH} {test_path}")
    else:
        init_db()
        upload_demo_data()
        os.system(f"cp {test_path} {BACKUP_DB_PATH}")


def db_path(app):
    return "forecast_app/" + app.config["SQLALCHEMY_DATABASE_URI"].split("///")[1]


@pytest.fixture(scope="session", autouse=True)
def cleanup(request):
    """Cleanup a database backup once we are finished."""

    def remove_backup_db():
        os.unlink(BACKUP_DB_PATH)

    request.addfinalizer(remove_backup_db)


@pytest.fixture(scope="session", autouse=True)
def setup_and_cleanup(request):
    # breakpoint()
    os.mkdir(TestingConfig.OUTPUT_DIR)
    os.mkdir(TestingConfig.UPLOAD_DIR)
    yield None
    shutil.rmtree(TestingConfig.OUTPUT_DIR)
    shutil.rmtree(TestingConfig.UPLOAD_DIR)


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


def pytest_configure():
    pytest.FIXTURE_DIR = Path(__file__).parent / "fixtures"
    pytest.load_demo_db = load_demo_db


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
