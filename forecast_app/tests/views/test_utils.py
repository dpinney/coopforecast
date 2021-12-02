import pandas as pd
import json
import pytest

from forecast_app.lib.utils import transform_timeseries_df_for_highcharts


def test_transform_timeseries_df_for_highcharts():
    df = pd.read_csv(
        pytest.test_data_path / "ercot-ncent-load.csv", parse_dates=["timestamp"]
    )
    test_array = transform_timeseries_df_for_highcharts(df, value="load")

    with open(pytest.test_data_path / "chart-formatted-load.json") as f:
        correct_array = json.load(f)

    assert test_array == correct_array
