import pandas as pd
import pytest

from forecast_app.views import (
    ForecastView,
    HistoricalLoadDataView,
    HistoricalWeatherDataView,
    ForecastWeatherDataView,
)
from forecast_app.models import ForecastModel
from forecast_app.executor import executor
from forecast_app.commands import upload_demo_data


def test_templates(auth, client):
    """Test that all pages return 200 and have the expected content"""

    pages = {
        "/historical-load-data": "Historical Load Data",
        "/forecast-weather-data": "Forecast Weather Data",
        "/historical-weather-data": "Historical Weather Data",
        "/forecast": "Latest Forecast",
        "/instructions": "Instructions",
        "/model-settings": "Model Settings",
        "/user-settings": "User Settings",
        "/forecast-models": "Forecast Models",
    }

    auth.login()
    for route, page_name in pages.items():
        response = client.get(route)
        assert response.status_code == 200
        assert page_name in str(response.data)

    # Test again but with data
    upload_demo_data()
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


class TestDataViews:
    classes = [
        ForecastWeatherDataView,
        HistoricalWeatherDataView,
        HistoricalLoadDataView,
    ]

    def test_get_chart(self):
        pass

    def test_get_table(self, db):
        for cls in self.classes:
            chart_array = cls().get_chart()
            assert type(chart_array) == list
            assert all([len(datapoint) == 2 for datapoint in chart_array])

    # Tested more thoroughly via test_templates


class TestForecastView:
    def test_get(self):
        pass

    def test_post(self, db, client, auth):
        auth.login()
        upload_demo_data(models=False)
        assert db.session.query(ForecastModel).count() == 0
        client.post("/forecast", data={"mock": "true"})
        assert db.session.query(ForecastModel).count() == 1
        # TEST KILLING PROCESS
        new_model = ForecastModel.query.first()

        # Ensure expected behavior immediately after lengthy job
        executor.futures._state(new_model.creation_date)
        assert not executor.futures.done(new_model.creation_date)
        assert new_model.is_running

        # Kill the processes / test ForecastModel.done_callback
        # TODO: This shutdown isn't effective (?), the tests wait for time.sleep
        #       to finish before moving on. But done_callback works.
        #       Using wait=False would probably solve this problem, but then we
        #       have to deal with multiple db sessions.
        #       https://www.pythoncentral.io/understanding-python-sqlalchemy-session/
        executor.shutdown()
        assert executor.futures.done(new_model.creation_date)
        assert not new_model.is_running

    def test_get_chart(self):
        pass

    def test_check_data_preparation(self):
        pass
