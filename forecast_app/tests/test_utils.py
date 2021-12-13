import pandas as pd
import json
import pytest

from forecast_app.utils import allowed_file, upload_file
from forecast_app.models import HistoricalData


def test_upload_file():
    pass
    # TODO: Test me


def test_allowed_file():
    assert allowed_file("test.csv")
    assert allowed_file("test.CSV")
    assert not allowed_file("test.xlsx")
