import pandas as pd
import pytest

from forecast_app.views import ForecastView, LoadDataView, WeatherDataView


# TODO: Ensure that all views can handle an empty database


class TestLoadDataView:
    def test_get_table(self):
        chart_array = LoadDataView().get_chart()
        assert type(chart_array) == list
        assert all([len(datapoint) == 2 for datapoint in chart_array])
        # Already tested by test_utils


class TestWeatherDataView:
    def test_init(self):
        WeatherDataView()

    # TODO: Test more thoroughly


class TestForecastView:
    def test_init(self):
        ForecastView()

    # TODO: Test more thoroughly
