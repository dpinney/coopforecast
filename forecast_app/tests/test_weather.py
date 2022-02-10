from datetime import date
from unittest.mock import patch
import pytest
import os
import filecmp
import pandas as pd

from forecast_app import create_app
from forecast_app.weather import AsosRequest, NwsForecastRequest


class TestAsosRequest:
    @pytest.mark.skip(
        reason="It's poor form to directly query API. Option to perform this in cli.py"
    )
    def test_asos_api():
        app = create_app("test")
        asos_request = AsosRequest(
            start_date=date(2022, 1, 1),
            end_date=date(2022, 1, 14),
            tz=app.config["TIMEZONE"],
            station=app.config["ASOS_STATION"],
        )

        request = asos_request.send_request()
        assert request.status_code == 200

        df = asos_request.create_df()
        assert not df.empty
        print("Response from ASOS ----------------------")
        print(df.head())
        print("-----------------------------------------")

    def test_send_request(self, app):
        with patch("requests.get", side_effect=pytest.mocked_asos_response) as mock_get:
            # Mock request to https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?station=ALO&data=tmpc&year1=2022&month1=1&day1=1&year2=2022&month2=1&day2=14&tz=America%2FNew_York&format=onlycomma&latlon=no&elev=no&missing=M&trace=T&direct=no&report_type=1&report_type=2
            asos_request = AsosRequest(
                start_date=date(2022, 1, 1),
                end_date=date(2022, 1, 14),
                tz=app.config["TIMEZONE"],
                station=app.config["ASOS_STATION"],
            )
            request = asos_request.send_request()
            assert request.status_code == 200
            assert request.text.startswith("station,valid,tmpc")

    def test_create_df(self):
        with patch("requests.get", side_effect=pytest.mocked_asos_response) as mock_get:
            asos_request = AsosRequest(
                start_date=date(2022, 1, 1), end_date=date(2022, 1, 14)
            )

            asos_request.send_request()
            df = asos_request.create_df()
            assert not df.empty
            assert df["tempc"].dtype == "float64"
            assert df.shape[0] == 312
            assert str(df.iloc[0].name) == "2022-01-01 01:00:00"
            assert df["tempc"].iloc[0] == -10.61
            assert not any(pd.isna(df["tempc"]))

    def test_write_response(self, app):
        with patch("requests.get", side_effect=pytest.mocked_asos_response) as mock_get:
            asos_request = AsosRequest(
                start_date=date(2022, 1, 1), end_date=date(2022, 1, 14)
            )
            request = asos_request.send_request()
            tmp_output_path = app.config["OUTPUT_DIR"] + "/asos-response.csv"
            mock_path = pytest.FIXTURE_DIR / "asos-response.csv"
            asos_request.write_response(tmp_output_path)
            assert os.path.exists(tmp_output_path)
            assert filecmp.cmp(mock_path, tmp_output_path)


class TestNwsForecastRequest:
    def test_send_request(self):
        with patch("requests.get", side_effect=pytest.mocked_nws_response) as mock_get:
            nws_request = NwsForecastRequest().send_request()
            assert nws_request.text.startswith("{")

    def test_create_df(self):
        with patch("requests.get", side_effect=pytest.mocked_nws_response) as mock_get:
            nws_request = NwsForecastRequest()
            nws_request.send_request()
            df = nws_request.create_df()
            assert df.shape[0] == 156
            assert df["tempc"].iloc[0] == 2.78

    def test_write_response(self, app):
        with patch("requests.get", side_effect=pytest.mocked_nws_response) as mock_get:
            nws_request = NwsForecastRequest()
            nws_request.send_request()
            tmp_output_path = app.config["OUTPUT_DIR"] + "/nws-response.json"
            mock_path = pytest.FIXTURE_DIR / "nws-response.json"
            nws_request.write_response(tmp_output_path)
            assert os.path.exists(tmp_output_path)
            assert filecmp.cmp(mock_path, tmp_output_path)

    def test_fahrenheit_to_celcius(self):
        assert NwsForecastRequest.fahrenheit_to_celcius(32) == 0
        assert NwsForecastRequest.fahrenheit_to_celcius(14) == -10

    @pytest.mark.skip(
        reason="It's poor form to directly query API. Option to perform this in cli.py"
    )
    def test_nws_api():
        app = create_app("test")
        nws_request = NwsForecastRequest(nws_code=app.config["NWS_CODE"])

        request = nws_request.send_request()
        assert request.status_code == 200

        df = nws_request.create_df()
        assert not df.empty
        print("Response from NWS ----------------------")
        print(df.head())
        print("----------------------------------------")
