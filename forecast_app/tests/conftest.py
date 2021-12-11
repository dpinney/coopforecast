import os
import tempfile
from pathlib import Path

import pytest

from forecast_app import create_app
from forecast_app.db import init_db
from forecast_app.commands import upload_demo_data

# TESTING CONFIG


@pytest.fixture
def app():
    return create_app(test_config={"TESTING": True})


@pytest.fixture
def client(app):
    db_fd, db_path = tempfile.mkstemp()

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_path
    os.environ["DATABASE_URL"] = db_path
    with app.test_client() as client:
        with app.app_context():
            init_db()
            upload_demo_data()  # TODO: Make this smaller
        yield client

    os.close(db_fd)
    os.unlink(db_path)


def pytest_configure():
    pass
