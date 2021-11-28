import os
import tempfile

import pytest

from forecast_app.web import app


@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp()

    with app.test_client() as client:
        yield client

    os.close(db_fd)
    os.unlink(db_path)


def test_login(client):
    """Check basic response from login page."""
    assert client.get("/").status_code == 200
