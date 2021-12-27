import pandas as pd
import json
import pytest
from unittest.mock import patch

import forecast_app
from forecast_app import create_app
from forecast_app.utils import allowed_file, upload_file

# TEST CONFIG
@patch("forecast_app.config.ProductionConfig.ADMIN_USER", None)
def test_admin_user_security():
    with pytest.raises(ValueError):
        _ = create_app("prod")


@patch("forecast_app.config.ProductionConfig.ADMIN_PASSWORD", None)
def test_admin_password_security():
    with pytest.raises(ValueError):
        _ = create_app("prod")


def test_upload_file():
    pass
    # TODO: Test me


def test_allowed_file():
    assert allowed_file("test.csv")
    assert allowed_file("test.CSV")
    assert not allowed_file("test.xlsx")
