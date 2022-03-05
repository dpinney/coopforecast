from unittest.mock import Mock

import pandas as pd
import pytest

from forecast_app.burtcoppd import get_on_and_off_peak_info


def test_get_on_and_off_peak_info():
    df = pd.read_csv(pytest.FIXTURE_DIR / "cached-dataframe.csv", parse_dates=["dates"])
    df = df.set_index("dates", drop=False)
    model = Mock(start_date=pd.Timestamp("2018-01-01"))
    info = get_on_and_off_peak_info(df, model)
    assert info is None

    model = Mock(start_date=pd.Timestamp("2018-12-21"))
    info = get_on_and_off_peak_info(df, model)
    assert info
    assert info["on_peak"]["max_load"] == pytest.approx(16960.682486)
    assert info["on_peak"]["timestamp"].month == 12
    assert info["off_peak"]["max_load"] == pytest.approx(17949.908233)
    assert info["off_peak"]["timestamp"].month == 12
