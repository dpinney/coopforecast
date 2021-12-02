import pandas as pd
import pytest

from forecast_app.lib.load_data import LoadData


class TestLoadData:
    @pytest.fixture(autouse=True, scope="class")
    def instance(self):
        print("CREATING NEW INSTANCE")
        return LoadData()

    def test_get_data(self, instance):
        assert type(instance.get_data()) == pd.DataFrame

    def test_get_table(self, instance):
        chart_array = instance.get_chart()
        assert type(chart_array) == list
        assert all([len(datapoint) == 2 for datapoint in chart_array])
        # Already tested by test_utils
