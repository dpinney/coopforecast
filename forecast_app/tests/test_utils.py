import os
import re
from datetime import datetime
from unittest.mock import patch

import pandas as pd
import pytest
from flask import request
from werkzeug.datastructures import FileStorage

import forecast_app
from forecast_app import create_app
from forecast_app.utils import allowed_file, prepare_filename_for_upload, upload_file


# TEST CONFIG
@patch("forecast_app.config.ProductionConfig.ADMIN_USER", None)
def test_admin_user_security():
    with pytest.raises(ValueError):
        _ = create_app("prod")


@patch("forecast_app.config.ProductionConfig.ADMIN_PASSWORD", None)
def test_admin_password_security():
    with pytest.raises(ValueError):
        _ = create_app("prod")


def test_upload_file(app):
    filename = "historical-load.csv"
    dest_path = os.path.join(
        app.config["UPLOAD_DIR"], prepare_filename_for_upload(filename)
    )
    assert not os.path.exists(dest_path)

    src_path = pytest.FIXTURE_DIR / filename
    name = "posted_file"
    mock_file = FileStorage(
        stream=open(src_path, "rb"),
        filename=filename,
        content_type="multipart/form-data",
    )
    with app.test_request_context("/foo", method="POST"):
        request.files = {name: mock_file}
        upload_file(name)

    assert os.path.exists(dest_path)
    df1 = pd.read_csv(dest_path)
    df2 = pd.read_csv(src_path)
    assert df1.equals(df2)


def test_allowed_file():
    assert allowed_file("test.csv")
    assert allowed_file("test.CSV")
    assert not allowed_file("test.foo")
    assert not allowed_file("test.txt")


def test_prepare_filename_for_upload():
    filename = "historical-load.test-t.t-t.csv"
    new_filename = prepare_filename_for_upload(filename)
    assert new_filename.endswith(".csv")
    assert new_filename.startswith("historical-load.test-t.t-t.")
    assert re.match(r"historical-load\.test-t\.t-t\..*\.csv", new_filename)
