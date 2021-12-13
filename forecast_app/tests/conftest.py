import os
import tempfile
from pathlib import Path

import pytest

from forecast_app import create_app
from forecast_app.commands import upload_demo_data
from forecast_app.db import init_db


@pytest.fixture
def app():
    return create_app(test_config={"TESTING": True})


@pytest.fixture
def client(app):
    db_fd, db_path = tempfile.mkstemp()

    os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(db_fd, "test.db")

    with app.test_client() as client:
        with app.app_context():
            init_db()
            upload_demo_data()  # TODO: Make this smaller
        yield client

    os.close(db_fd)
    os.unlink(db_path)


def pytest_configure():
    pass
