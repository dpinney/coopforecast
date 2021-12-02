import os
import tempfile
from pathlib import Path

import pytest

from forecast_app.web import app


@pytest.fixture
def client():
    """A test client for the app."""
    return app.test_client()


def pytest_configure():
    pytest.test_data_path = Path("forecast_app") / "static" / "test-data"
