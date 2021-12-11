from sqlalchemy import Column, Integer, Float, String, DateTime
from forecast_app.db import Base
from forecast_app.utils import get_or_create


class HistoricalData(Base):
    __tablename__ = "historical_data"
    milliseconds = Column(Integer, primary_key=True)
    load = Column(Float)
    timestamp = Column(DateTime)
    tempc = Column(Float)

    def __init__(self, timestamp=None, load=None, tempc=None):
        if not timestamp:
            raise Exception("timestamp is a required field")
        self.load = load
        self.timestamp = timestamp
        self.milliseconds = timestamp.timestamp() * 1000
        self.tempc = tempc

    def __repr__(self):
        return f"<Historical {self.timestamp}: Load {self.load}, Temperature (°C) {self.tempc}>"


class ForecastData(Base):
    __tablename__ = "forecast_data"
    milliseconds = Column(Integer, primary_key=True)
    load = Column(Float)
    timestamp = Column(DateTime)
    tempc = Column(Float)

    def __init__(self, timestamp=None, load=None, tempc=None):
        if not timestamp:
            raise Exception("timestamp is a required field")
        self.load = load
        self.timestamp = timestamp
        self.milliseconds = timestamp.timestamp() * 1000
        self.tempc = tempc

    def __repr__(self):
        return f"<Forecast {self.timestamp}: Load {self.load}, Temperature (°C) {self.tempc}>"

    @classmethod
    def ingest_data_from_csv(cls, filename):
        # TODO: validation should happen here
        get_or_create(cls, timestamp=datetime.datetime.now(), load=0, tempc=0)
