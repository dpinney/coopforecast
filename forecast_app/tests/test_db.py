from datetime import datetime

from forecast_app.models import HistoricalLoadData


def test_db_init(db):
    assert db.engine is not None
    assert db.session is not None


def test_teardown(db):
    HistoricalLoadData.query.count() == 0
    historical_data = HistoricalLoadData(timestamp=datetime(2020, 1, 1), value=1)
    db.session.add(historical_data)
    db.session.commit()
    assert HistoricalLoadData.query.count() == 1


def test_teardown2(db):
    """Ensure that the database is empty at the end of each test."""
    HistoricalLoadData.query.count() == 0
    historical_data = HistoricalLoadData(timestamp=datetime(2020, 1, 1), value=1)
    db.session.add(historical_data)
    db.session.commit()
    assert HistoricalLoadData.query.count() == 1
