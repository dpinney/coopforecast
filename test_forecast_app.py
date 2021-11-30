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


class TestViews:
    def test_login(self, client):
        """Check basic response from login page."""
        assert client.get("/").status_code == 200

    def test_load_data(self, client):
        """Check basic response from load data page."""
        assert client.get("/load-data").status_code == 200

    def test_weather_data(self, client):
        """Check basic response from weather data page."""
        assert client.get("/weather-data").status_code == 200

    def test_forecast(self, client):
        """Check basic response from forecast page."""
        assert client.get("/forecast").status_code == 200

    def test_instructions(self, client):
        """Check basic response from instructions page."""
        assert client.get("/instructions").status_code == 200

    def test_model_settings(self, client):
        """Check basic response from model settings page."""
        assert client.get("/model-settings").status_code == 200

    def test_user_settings(self, client):
        """Check basic response from user settings page."""
        assert client.get("/user-settings").status_code == 200
