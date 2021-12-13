from datetime import datetime
from forecast_app.models import HistoricalData


def test_db_init(db):
    assert db.engine is not None
    assert db.session is not None


def test_teardown(db):
    HistoricalData.query.count() == 0
    historical_data = HistoricalData(timestamp=datetime(2020, 1, 1), load=1)
    db.session.add(historical_data)
    db.session.commit()
    assert HistoricalData.query.count() == 1


def test_teardown2(db):
    HistoricalData.query.count() == 0
    historical_data = HistoricalData(timestamp=datetime(2020, 1, 1), load=1)
    db.session.add(historical_data)
    db.session.commit()
    assert HistoricalData.query.count() == 1
