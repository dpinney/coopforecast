import pytest
from datetime import datetime
import pandas as pd
import os
from multiprocessing import Process
import signal
from time import sleep

from forecast_app.models import (
    HistoricalLoadData,
    HistoricalWeatherData,
    ForecastWeatherData,
    ForecastModel,
)

# TODO: Test that submitting a temperature csv to the load data view works

# Quick code snippet to get inside subprocesses
# def test_subprocess(app, db):
#     pytest.load_demo_db(app)
#     new_model = ForecastModel()
#     breakpoint()


class TestHistoricalLoadData:
    def test_load_data(self, db, app):
        fixture_path = pytest.FIXTURE_DIR / "uncontinuous.csv"
        HistoricalLoadData.load_data(fixture_path)
        assert pd.isna(HistoricalLoadData.query.get(datetime(2002, 1, 1, 6)).value)
        assert HistoricalLoadData.query.count() == 72

        fixture_path = pytest.FIXTURE_DIR / "historical-load.csv"
        HistoricalLoadData.load_data(fixture_path)
        obj = HistoricalLoadData.query.get(datetime(2002, 1, 1, 3))
        assert obj
        assert obj.value == 10081
        obj = HistoricalLoadData.query.get(datetime(2002, 1, 2, 12))
        assert obj
        assert obj.value == 13319

        fixture_path = pytest.FIXTURE_DIR / "historical-load-update.csv"
        HistoricalLoadData.load_data(fixture_path)
        assert HistoricalLoadData.query.get(datetime(2002, 1, 1, 3)).value == 42
        # ensure that values in between the timestamps aren't overwritten with NaN
        assert not pd.isna(HistoricalLoadData.query.get(datetime(2002, 1, 1, 5)).value)

    def test_init(self, db):
        obj = HistoricalLoadData(timestamp=datetime(2020, 1, 1), value=42.0)
        db.session.add(obj)
        db.session.commit()
        assert HistoricalLoadData.query.count() == 1

        assert obj.timestamp.timestamp() * 1000 == obj.milliseconds


class TestHistoricalWeatherData:
    def test_load_data(self, db):
        assert HistoricalWeatherData.query.get(datetime(2002, 1, 1)) is None
        fixture_path = pytest.FIXTURE_DIR / "historical-weather.csv"
        HistoricalWeatherData.load_data(fixture_path)
        obj = HistoricalWeatherData.query.get(datetime(2019, 1, 1, 0))
        assert obj
        assert obj.value == 4.12
        obj = HistoricalWeatherData.query.get(datetime(2019, 1, 1, 14))
        assert obj
        assert obj.value == 5.25

    def test_init(self, db):
        obj = HistoricalWeatherData(timestamp=datetime(2020, 1, 1), value=42.0)
        db.session.add(obj)
        db.session.commit()
        assert HistoricalWeatherData.query.count() == 1

        assert obj.timestamp.timestamp() * 1000 == obj.milliseconds


class TestForecastWeatherData:
    def test_load_data(self, db):
        assert ForecastWeatherData.query.get(datetime(2002, 1, 1)) is None
        fixture_path = pytest.FIXTURE_DIR / "historical-weather.csv"
        ForecastWeatherData.load_data(fixture_path)
        obj = ForecastWeatherData.query.get(datetime(2019, 1, 1, 0))
        assert obj
        assert obj.value == 4.12
        obj = ForecastWeatherData.query.get(datetime(2019, 1, 1, 14))
        assert obj
        assert obj.value == 5.25

    def test_init(self, db):
        obj = ForecastWeatherData(timestamp=datetime(2020, 1, 1), value=42.0)
        db.session.add(obj)
        db.session.commit()
        assert ForecastWeatherData.query.count() == 1

        assert obj.timestamp.timestamp() * 1000 == obj.milliseconds


class TestForecastModel:
    # NOTE: test_is_prepared is below

    def test_init(self, db, app):
        # Raise an error if the model is created with an empty database
        with pytest.raises(Exception):
            ForecastModel()

        pytest.load_demo_db(app)
        model = ForecastModel()
        assert os.path.exists(model.output_dir)

    def test_timestamps(self):
        pass

    def test_subprocessing(self, app, db):
        pytest.load_demo_db(app)
        new_model = ForecastModel()
        assert not new_model.is_running
        assert new_model.exited_successfully is None
        assert not os.path.exists(new_model.process_file)

        process = Process(target=new_model.launch_model)
        process.start()
        new_model.store_process_id(process.pid)
        assert new_model.is_running
        assert new_model.exited_successfully is None
        assert os.path.exists(new_model.process_file)
        assert new_model.get_process_id() == str(process.pid)

        new_model.cancel()
        sleep(2)  # Give the process time to cancel
        assert process.exitcode == -signal.SIGKILL
        assert not new_model.is_running
        assert new_model.exited_successfully is False

    def test_launch_model(self):
        pass

    def test_df(self, app, db):
        pytest.load_demo_db(app)
        model = ForecastModel()
        assert os.path.exists(os.path.join(model.output_dir, ForecastModel.df_filename))
        df = model.get_df()
        assert not any(["Unnamed" in col for col in df.columns])

    def test_collect_training_data(self, app, db):
        pytest.load_demo_db(app)
        model = ForecastModel.query.first()
        model_df = model.get_df()
        assert pd.isnull(model_df.tail(1).load.values[0])
        model_df = model_df.set_index("dates")
        assert pd.isna(model_df.loc[datetime(2019, 1, 1), "load"])
        assert model_df.shape[0] == HistoricalLoadData.to_df().shape[0] + 24


def test_is_prepared(app, db):
    # Combine tests to make tests faster
    # FORECAST MODEL

    for cls in [ForecastWeatherData, HistoricalWeatherData, HistoricalLoadData]:
        is_prepared = cls.is_prepared()
        assert not is_prepared

    pytest.load_demo_db(app)

    # FORECAST MODEL
    is_prepared = ForecastModel.is_prepared()
    assert is_prepared
    assert is_prepared["start_date"] == datetime(2019, 1, 1, 0)
    assert is_prepared["end_date"] == datetime(2019, 1, 1, 23)
    # FORECAST DATA
    is_prepared = ForecastWeatherData.is_prepared()
    assert is_prepared
    assert is_prepared["start_date"] == datetime(2019, 1, 1, 0)
    assert is_prepared["end_date"] == datetime(2019, 1, 1, 23)
    # HISTORICAL DATA
    is_prepared = HistoricalLoadData.is_prepared()
    assert is_prepared
    assert is_prepared["start_date"] == datetime(2014, 1, 1, 0)
    assert is_prepared["end_date"] == datetime(2018, 12, 31, 23)
    is_prepared = HistoricalWeatherData.is_prepared()
    assert is_prepared
    assert is_prepared["start_date"] == datetime(2014, 1, 1, 0)
    assert is_prepared["end_date"] == datetime(2019, 1, 1, 10, 0)


def test_to_df(app, db):
    # Combine tests to make tests faster
    # Works on an empty database
    dfs = [
        ForecastWeatherData.to_df(),
        HistoricalWeatherData.to_df(),
        HistoricalLoadData.to_df(),
    ]
    assert all([df.empty for df in dfs])

    # ... and on a populated database
    pytest.load_demo_db(app)

    dfs = [
        ForecastWeatherData.to_df(),
        HistoricalWeatherData.to_df(),
        HistoricalLoadData.to_df(),
    ]
    assert all([df.shape[0] > 20 for df in dfs])
