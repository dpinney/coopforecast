from sqlalchemy import Column, Integer, Float, String, DateTime
from forecast_app.db import Base


class HistoricalData(Base):
    __tablename__ = "historical_data"
    seconds = Column(Integer, primary_key=True)
    load = Column(Float)
    timestamp = Column(DateTime)
    weather = Column(Float)

    def __init__(self, timestamp_dt=None, load=None, weather=None):
        if not timestamp_dt:
            raise Exception("timestamp_dt is a required field")
        self.load = load
        self.timestamp = timestamp_dt
        self.seconds = timestamp_dt.timestamp()
        self.weather = weather

    def __repr__(self):
        return (
            f"<Historical {self.timestamp}: Load {self.load}, Weather {self.weather}>"
        )


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    email = Column(String(120), unique=True)

    def __init__(self, name=None, email=None):
        self.name = name
        self.email = email

    def __repr__(self):
        return f"<User {self.name!r}>"
