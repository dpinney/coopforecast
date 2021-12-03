import os
import tempfile
from pathlib import Path

import pytest

from forecast_app import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


def pytest_configure():
    pass
