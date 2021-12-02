import pandas as pd
import pytest

from forecast_app.views import LoadDataView, WeatherDataView


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
