from datetime import datetime

from forecast_app.models import HistoricalData, ForecastData


class TestHistoricalData:
    def test_ingest_data_from_csv(self):
        # HistoricalData.ingest_data_from_csv()
        pass

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
