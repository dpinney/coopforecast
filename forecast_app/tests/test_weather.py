from datetime import date
from unittest.mock import patch
import pytest

from forecast_app import create_app
from forecast_app.weather import pull_asos


def test_get_asos_station():
    pass


@pytest.mark.skip(
    reason="It's poor form to directly query API. Option to perform this in cli.py"
)
def test_asos_api():
    app = create_app("dev")
    df = pull_asos(
        start_date=date(2022, 1, 1),
        end_date=date(2022, 1, 14),
        tz=app.config["TIMEZONE"],
        station=app.config["ASOS_STATION"],
    )
    assert not df.empty
    assert df["station"].iloc[0] == app.config["ASOS_STATION"]


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
    df = pull_asos(
        start_date=date(2022, 1, 1),
        end_date=date(2022, 1, 14),
        tz=app.config["TIMEZONE"],
        station=app.config["ASOS_STATION"],
    )
    assert df["valid"].dtype == "datetime64[ns]"
    assert df["tmpc"].dtype == "float64"
    assert df.shape[0] == 361
