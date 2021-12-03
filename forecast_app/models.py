from sqlalchemy import Column, Integer, Float, String, DateTime
from forecast_app.db import Base


class HistoricalData(Base):
    __tablename__ = "historical_data"
    milliseconds = Column(Integer, primary_key=True)
    load = Column(Float)
    timestamp = Column(DateTime)
    weather = Column(Float)

    def __init__(self, timestamp_dt=None, load=None, weather=None):
        if not timestamp_dt:
            raise Exception("timestamp_dt is a required field")
        self.load = load
        self.timestamp = timestamp_dt
        self.milliseconds = timestamp_dt.timestamp() * 1000
        self.weather = weather

    def __repr__(self):
        return (
            f"<Historical {self.timestamp}: Load {self.load}, Weather {self.weather}>"
        )
