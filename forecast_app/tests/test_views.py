import pandas as pd
from flask import request
import pytest
from werkzeug.datastructures import FileStorage
from datetime import date, datetime

from forecast_app.views import (
    ForecastModelDetailView,
    LatestForecastView,
    ForecastWeatherDataSync,
    HistoricalLoadDataView,
    HistoricalWeatherDataSync,
    HistoricalWeatherDataView,
    ForecastWeatherDataView,
)
from forecast_app.models import (
    ForecastModel,
    ForecastWeatherData,
    HistoricalWeatherData,
    HistoricalLoadData,
)
from forecast_app.commands import upload_demo_data, init_db


def test_templates(app, auth, client):
    """Test that all pages return 200 and have the expected content"""

    pages = {
        "/historical-load-data": "Historical Load Data",
        "/forecast-weather-data": "Forecast Weather Data",
        "/historical-weather-data": "Historical Weather Data",
        "/latest-forecast": "Latest Forecast",
        "/instructions": "Instructions",
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

    # latest-forecast page has a different format after adding data
    pages["/latest-forecast"] = "Forecast"

    for route, page_name in pages.items():
        response = client.get(route)
        assert response.status_code == 200
        assert page_name in str(response.data)


def test_permissions(app, client, auth):
    # Test that if you're logged out, you are redirected to the root page
    all_routes = set([rule_obj.rule for rule_obj in app.url_map.iter_rules()])
    all_routes -= set(
        ["/", "/login", "/logout", "/static/<path:filename>", "/500-trigger"]
    )
    for route in all_routes:
        response = client.get(route, follow_redirects=True)
        assert response.status_code == 200, route
        assert response.request.path == "/", route


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

    def test_get_missing_value_summary(self, db):
        fixture_path = pytest.FIXTURE_DIR / "uncontinuous.csv"
        HistoricalLoadData.load_data(fixture_path)
        summary = HistoricalLoadDataView().get_missing_values_summary()
        assert summary["count"] == 6
        assert summary["start_datetime"] == datetime(2002, 1, 3, 6, 0, 0)
        assert summary["end_datetime"] == datetime(2002, 1, 3, 8, 0, 0)
        assert summary["max_span"] == 3

    def test_get_table(self):
        # TODO: Test that descending order
        pass

    def test_get_summary(self, db, app):
        for cls in self.classes:
            summary = cls().get_summary()
            assert summary is None

        pytest.load_demo_db(app)
        forecast_summary = ForecastWeatherDataView().get_summary()
        assert forecast_summary["count"] == 24
        assert forecast_summary["start_datetime"] == datetime(2019, 1, 1, 0, 0, 0)
        assert forecast_summary["end_datetime"] == datetime(2019, 1, 1, 23, 0, 0)
        assert forecast_summary["missing_values"]["count"] == 0

        init_db()
        HistoricalLoadData.load_data(pytest.FIXTURE_DIR / "uncontinuous.csv")
        load_summary = HistoricalLoadDataView().get_summary()
        assert load_summary["missing_values"]["count"] == 6

    def test_get_chart(self, db, app):
        for cls in self.classes:
            chart_array = cls().get_chart()
            assert not chart_array[0]["data"]

        pytest.load_demo_db(app)
        for cls in self.classes:
            chart = cls().get_chart()
            assert type(chart[0]) == dict
            assert all([len(datapoint) == 2 for datapoint in chart[0]["data"]])

    def post_data_view(self, cls, filename=None, final_count=None):
        src_path = pytest.FIXTURE_DIR / filename
        # Ensure that there is no data in the db
        cls.model.query.delete()
        assert cls.model.query.count() == 0
        upload_file = FileStorage(
            stream=open(src_path, "rb"),
            filename=src_path.name,
            content_type="multipart/form-data",
        )
        with self.app.test_request_context("/forecast-weather-data", method="POST"):
            request.files = {"file": upload_file}
            cls().post()

        assert cls.model.query.count() == final_count

    def test_data_post(self, db, app, client, auth):
        self.app = app
        self.post_data_view(
            ForecastWeatherDataView, filename="weather-forecast.csv", final_count=23
        )
        self.post_data_view(
            HistoricalWeatherDataView, filename="weather-forecast.csv", final_count=23
        )
        self.post_data_view(
            HistoricalLoadDataView, filename="historical-load.csv", final_count=72
        )

    # Tested more thoroughly via test_templates


class TestForecastView:
    def test_get(self):
        pass

    def test_get_chart(self):
        pass

    def test_check_data_preparation(self):
        pass


class TestForecastListView:
    def test_post(self, app, db, client, auth):
        auth.login()
        upload_demo_data(models=False)
        assert ForecastModel.query.count() == 0
        client.post("/forecast-models", data={"mock": "true"})
        # TODO: mock this instead
        assert ForecastModel.query.count() == 1
        # See test_subprocessing for more tests

    def test_get(self):
        pass


class TestForecastModelDetailView:
    def test_get(self):
        pass

    def test_post(self, app, db, client, auth):
        auth.login()
        upload_demo_data(models=False)
        assert ForecastModel.query.count() == 0
        client.post("/forecast-models", data={"mock": "true"})
        assert ForecastModel.query.count() == 1
        model = ForecastModel.query.first()
        client.post(f"/forecast-models/{model.slug}")
        assert not model.is_running
        assert model.status == "Failed"


class TestHistoricalWeatherDataSync:
    def test_build_request(self, app, db):
        request = HistoricalWeatherDataSync().build_request()
        assert request.start_date == app.config["EARLIEST_SYNC_DATE"]

        pytest.load_demo_db(app)

        request = HistoricalWeatherDataSync().build_request()
        assert request.start_date == date(2019, 1, 1)

    def test_post(self, app, client, auth, db):
        auth.login()
        with pytest.asos_patch:
            response = client.post(HistoricalWeatherDataSync.view_url)
        assert response.status_code == 302
        assert HistoricalWeatherData.query.count() == 312


class TestForecastWeatherDataSync:
    def test_build_request(self, app, db):
        request = ForecastWeatherDataSync().build_request()
        assert request.nws_code == app.config["NWS_CODE"]

    def test_post(self, app, client, auth, db):
        auth.login()
        with pytest.nws_patch:
            response = client.post(ForecastWeatherDataSync.view_url)
        assert response.status_code == 302
        assert ForecastWeatherData.query.count() == 156
