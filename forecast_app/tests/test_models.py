import pytest
from datetime import datetime

from forecast_app.models import HistoricalData, ForecastData, ForecastModel


class TestHistoricalData:
    def test_ingest_data_from_csv(self):
        # HistoricalData.ingest_data_from_csv()
        pass

    def test_load_data(self, db):
        assert HistoricalData.query.get(datetime(2002, 1, 1)) is None
        fixture_path = pytest.FIXTURE_DIR / "historical-load.csv"
        HistoricalData.load_data(fixture_path)
        obj = HistoricalData.query.get(datetime(2002, 1, 1, 3))
        assert obj
        assert obj.load == 10081
        obj = HistoricalData.query.get(datetime(2002, 1, 2, 12))
        assert obj
        assert obj.load == 13319

        # Ensure that a user can update the data
        fixture_path2 = pytest.FIXTURE_DIR / "historical-load-update.csv"
        HistoricalData.load_data(fixture_path2)
        obj = HistoricalData.query.get(datetime(2002, 1, 2, 12))
        assert obj
        assert obj.load == 43

    def test_init(self, db):
        new_object = HistoricalData(
            timestamp=datetime(2020, 1, 1), load=42.0, tempc=42.0
        )
        db.session.add(new_object)
        db.session.commit()
        assert HistoricalData.query.count() == 1

        assert new_object.timestamp.timestamp() * 1000 == new_object.milliseconds


class TestForecastData:
    def test_init(self, db):
        new_object = ForecastData(timestamp=datetime(2020, 1, 1), load=42.0, tempc=42.0)
        db.session.add(new_object)
        db.session.commit()
        assert ForecastData.query.count() == 1

        assert new_object.timestamp.timestamp() * 1000 == new_object.milliseconds

    def test_load_data(self):
        pass


class TestForecastModel:
    def test_init(self):
        pass

    def test_timestamps(self):
        pass

    def test_launch_model(self):
        pass


def test_is_prepared(app, db):
    # Combine tests to make tests faster
    # FORECAST MODEL
    is_prepared, start_date, end_date = ForecastModel.is_prepared()
    assert is_prepared is False
    assert start_date is None and end_date is None
    # FORECAST DATA
    is_prepared, start_date, end_date = ForecastData.is_prepared()
    assert is_prepared is False
    assert start_date is None and end_date is None
    # HISTORICAL DATA
    is_prepared, start_date, end_date = HistoricalData.is_prepared()
    assert is_prepared is False
    assert start_date is None and end_date is None

    pytest.load_demo_db(app)

    # FORECAST MODEL
    is_prepared, start_date, end_date = ForecastModel.is_prepared()
    assert is_prepared is True
    assert start_date == datetime(2019, 1, 1, 0)
    assert end_date == datetime(2019, 1, 1, 23)
    # FORECAST DATA
    is_prepared, start_date, end_date = ForecastData.is_prepared()
    assert is_prepared is True
    assert start_date == datetime(2019, 1, 1, 0)
    assert end_date == datetime(2019, 1, 1, 23)
    # HISTORICAL DATA
    is_prepared, start_date, end_date = HistoricalData.is_prepared()
    assert is_prepared is True
    assert start_date == datetime(2002, 1, 1, 0)
    assert end_date == datetime(2018, 12, 31, 23)


def test_to_df(app, db):
    # Combine tests to make tests faster
    # Works on an empty database
    # FORECAST DATA
    df = ForecastData.to_df()
    assert df.empty
    # HISTORICAL DATA
    df = HistoricalData.to_df()
    assert df.empty

    # ... and on a populated database
    pytest.load_demo_db(app)

    # FORECAST DATA
    df = ForecastData.to_df()
    assert df.shape[0] > 20
    df = HistoricalData.to_df()
    assert df.shape[0] > 1000
