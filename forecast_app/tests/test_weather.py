from datetime import date
from unittest.mock import patch
import pytest

from forecast_app.weather import get_asos_station, pull_asos


def test_get_asos_station():
    pass


def mocked_requests_get(*args, **kwargs):
    # https://stackoverflow.com/questions/15753390/how-can-i-mock-requests-and-the-response
    class MockResponse:
        def __init__(self, mock_path, status_code):
            self.status_code = status_code
            with open(mock_path, "r") as f:
                self.text = f.read()

    mock_path = pytest.FIXTURE_DIR / "asos-response.csv"
    return MockResponse(mock_path, 200)


@patch("requests.get", side_effect=mocked_requests_get)
def test_pull_asos(mock_get):
    # Mock request to https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?station=ALO&data=tmpc&year1=2022&month1=1&day1=1&year2=2022&month2=1&day2=14&tz=America%2FNew_York&format=onlycomma&latlon=no&elev=no&missing=M&trace=T&direct=no&report_type=1&report_type=2
    zipcode = "00000"

    df = pull_asos(date(2022, 1, 1), date(2022, 1, 14), zipcode)
    assert df["valid"].dtype == "datetime64[ns]"
    assert df["tmpc"].dtype == "float64"
    assert df.shape[0] == 361
