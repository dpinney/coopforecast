import pandas as pd
from flask import request
import pytest
from werkzeug.datastructures import FileStorage
from forecast_app.views import (
    ForecastView,
    HistoricalLoadDataView,
    HistoricalWeatherDataView,
    ForecastWeatherDataView,
)
from forecast_app.models import ForecastModel, ForecastData
from forecast_app.commands import upload_demo_data


def test_templates(app, auth, client):
    """Test that all pages return 200 and have the expected content"""

    pages = {
        "/historical-load-data": "Historical Load Data",
        "/forecast-weather-data": "Forecast Weather Data",
        "/historical-weather-data": "Historical Weather Data",
        "/latest-forecast": "Latest Forecast",
        "/instructions": "Instructions",
        "/model-settings": "Model Settings",
        "/user-settings": "User Settings",
        "/forecast-models": "Forecast Models",
    }

    auth.login()
    for route, page_name in pages.items():
        response = client.get(route)
        assert response.status_code == 200, f"{route} returned {response.status_code}"
        assert page_name in str(response.data)

    # Test again but with data
    pytest.load_demo_db(app)
    # Add model detail to pages to test
    for model in ForecastModel.query.all():
        pages[f"/forecast-models/{model.slug}"] = model.slug

    for route, page_name in pages.items():
        response = client.get(route)
        assert response.status_code == 200
        assert page_name in str(response.data)

    # Test again without having logged in
    auth.logout()
    for route, page_name in pages.items():
        response = client.get(route)
        assert response.status_code == 401, page_name


class TestLoginView:
    def test_get(self, auth, client):
        # Test that logged in users are redirected to latest forecast
        auth.login()
        response = client.get("/")
        assert response.status_code == 302
        response = client.get("/", follow_redirects=True)
        assert response.status_code == 200
        assert "Latest Forecast" in str(response.data)

        auth.logout()
        response = client.get("/")
        assert response.status_code == 200
        assert "Enter Username" in str(response.data)


class TestLogoutView:
    def test_get(self, auth, client):
        # Test that logged in users are redirected to latest forecast
        auth.login()
        response = client.get("/logout")
        assert response.status_code == 302
        auth.login()
        response = client.get("/logout", follow_redirects=True)
        assert response.status_code == 200
        assert "Enter Username" in str(response.data)


class TestDataViews:
    classes = [
        ForecastWeatherDataView,
        HistoricalWeatherDataView,
        HistoricalLoadDataView,
    ]

    def test_get_table(self):
        pass

    def test_get_chart(self, db, app):
        for cls in self.classes:
            chart_array = cls().get_chart()
            assert not chart_array

        pytest.load_demo_db(app)
        for cls in self.classes:
            chart_array = cls().get_chart()
            assert type(chart_array) == list
            assert all([len(datapoint) == 2 for datapoint in chart_array])

    def test_data_post(self, db, app, client, auth):
        src_path = pytest.FIXTURE_DIR / "weather-forecast.csv"

        # Ensure that there is no data in the db
        assert ForecastData.query.count() == 0
        upload_file = FileStorage(
            stream=open(src_path, "rb"),
            filename=src_path.name,
            content_type="multipart/form-data",
        )
        with app.test_request_context("/forecast-weather-data", method="POST"):
            request.files = {"file": upload_file}
            ForecastWeatherDataView().post()

        assert ForecastData.query.count() == 23

    # Tested more thoroughly via test_templates


class TestForecastView:
    def test_get(self):
        pass

    def test_post(self, app, db, client, auth):
        auth.login()
        upload_demo_data(models=False)
        assert ForecastModel.query.count() == 0
        client.post("/latest-forecast", data={"mock": "true"})
        # TODO: mock this instead
        assert ForecastModel.query.count() == 1
        # See test_subprocessing for more tests

    def test_get_chart(self):
        pass

    def test_check_data_preparation(self):
        pass


class TestForecastListView:
    def test_post(self):
        pass

    def test_get(self):
        pass


class TestForecastDetailView:
    def test_get(self):
        pass

    def test_post(self):
        pass
