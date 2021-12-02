import os
import tempfile

import pytest

from forecast_app.web import app


@pytest.fixture
def client():
    """A test client for the app."""
    return app.test_client()
