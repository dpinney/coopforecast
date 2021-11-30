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


def test_views(client):
    """Test that all pages return 200 and have the expected content"""

    pages = {
        "/": "Login",
        "/load-data": "Load Data",
        "/weather-data": "Weather Data",
        "/forecast": "Forecast",
        "/instructions": "Instructions",
        "/model-settings": "Model Settings",
        "/user-settings": "User Settings",
    }

    for route, page_name in pages.items():
        response = client.get(route)
        assert response.status_code == 200
        assert page_name in str(response.data)
