import datetime
import pandas as pd
from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

from forecast_app.db import db


class HistoricalData(db.Model):
    __tablename__ = "historical_data"
    milliseconds = Column(Integer)
    load = Column(Float)
    timestamp = Column(DateTime, primary_key=True)
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

    @classmethod
    def load_data(cls, filepath, columns=None):
        return _load_data(cls, filepath, columns)


class ForecastData(db.Model):
    __tablename__ = "forecast_data"
    milliseconds = Column(Integer)
    load = Column(Float)
    timestamp = Column(DateTime, primary_key=True)
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
    def load_data(cls, filepath, columns=None):
        return _load_data(cls, filepath, columns)


def _load_data(cls, filepath, columns=None):
    # NOTE: Entering a csv with both weather and load will overwrite both.
    #  Use columns var to ensure that only intended data is loaded?
    # TODO: validation should happen here
    df = pd.read_csv(filepath, parse_dates=["timestamp"])
    if columns:
        df = df[columns]

    # If uploading data for the first time, don't perform tens of thousands of queries
    if cls.query.count() == 0:
        for _, row in df.iterrows():
            instance = cls(
                timestamp=row["timestamp"],
                load=row.get("load"),
                tempc=row.get("tempc"),
            )
            db.session.add(instance)
        db.session.commit()
    else:
        for _, row in df.iterrows():
            instance = cls.query.get(row["timestamp"])
            if instance:
                instance.load = row.get("load", instance.load)
                instance.tempc = row.get("tempc", instance.tempc)
            else:
                instance = cls(
                    timestamp=row["timestamp"],
                    load=row.get("load"),
                    tempc=row.get("tempc"),
                )
            db.session.add(instance)
        db.session.commit()

    return [
        {
            "level": "success",
            "text": f"Success! Loaded {len(df)} historical data points",
        }
    ]
