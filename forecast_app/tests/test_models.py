from datetime import datetime

from forecast_app.models import HistoricalData
from forecast_app.db import session


class TestHistoricalData:
    def test_ingest_data_from_csv(self):
        # HistoricalData.ingest_data_from_csv()
        pass

    def test_create_object(self):
        HistoricalData(timestamp=datetime(2020, 1, 1), load=42.0, tempc=42.0)
        session.commit()
        assert HistoricalData.query.count() == 1
