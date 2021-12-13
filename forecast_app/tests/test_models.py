import pytest
from datetime import datetime

from forecast_app.models import HistoricalData, ForecastData


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
