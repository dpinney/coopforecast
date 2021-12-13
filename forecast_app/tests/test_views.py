import pandas as pd
import pytest

from forecast_app.views import ForecastView, LoadDataView, WeatherDataView


class TestLoadDataView:
    def test_get_table(self, db):
        chart_array = LoadDataView().get_chart()
        assert type(chart_array) == list
        assert all([len(datapoint) == 2 for datapoint in chart_array])
        # Already tested by test_utils

    # TODO: Test that a post request shows the correct messages


class TestWeatherDataView:
    def test_init(self):
        WeatherDataView()

    # Tested more thoroughly via test_templates


class TestForecastView:
    def test_init(self):
        ForecastView()

    # Tested more thoroughly via test_templates
