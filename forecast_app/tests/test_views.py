import pandas as pd
import pytest

from forecast_app.views import (
    ForecastView,
    LoadDataView,
    HistoricalWeatherDataView,
    ForecastWeatherDataView,
)


class TestLoadDataView:
    def test_get_table(self, db):
        chart_array = LoadDataView().get_chart()
        assert type(chart_array) == list
        assert all([len(datapoint) == 2 for datapoint in chart_array])
        # Already tested by test_utils

    # TODO: Test that a post request shows the correct messages


class TestHistoricalWeatherDataView:
    def test_init(self):
        HistoricalWeatherDataView()

    # Tested more thoroughly via test_templates


class TestForecastWeatherDataView:
    def test_init(self):
        ForecastWeatherDataView()

    # Tested more thoroughly via test_templates


class TestForecastView:
    def test_init(self):
        ForecastView()

    # Tested more thoroughly via test_templates
