import os
import datetime
import pandas as pd
from sqlalchemy import Column, Integer, Float, String, DateTime, JSON, Boolean
from flask_login import UserMixin

from forecast_app.db import db
import forecast_app.forecast as lf


class ForecastModel(db.Model):
    __tablename__ = "forecast_model"
    creation_date = Column(DateTime, default=datetime.datetime.utcnow, primary_key=True)
    # timestamps = Column(JSON, nullable=False)
    milliseconds = Column(JSON, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    tempcs = Column(JSON, nullable=False)
    is_running = Column(Boolean, nullable=False)
    model_path = Column(String, nullable=False)
    accuracy = Column(JSON)
    loads = Column(JSON)
    exited_successfully = Column(Boolean)
    epochs = 1  # TODO: Config epochs

    def __init__(self):
        # NOTE: Object is initialized from state of the database
        OUTPUT_DIR = "./forecast_app/static/output/"  # TODO: Config output dir
        self.model_path = os.path.join(OUTPUT_DIR, f"{self.creation_date}.h5")
        self.tempcs = [
            row.tempc for row in ForecastData.query.all()
        ]  # Ensure length is appropriate
        # NOTE: Cannot JSON serialize datetime objects
        timestamps = [row.timestamp for row in ForecastData.query.all()]
        self.milliseconds = [row.milliseconds for row in ForecastData.query.all()]
        self.start_date = sorted(timestamps)[0]
        self.end_date = sorted(timestamps)[-1]
        self.is_running = False
        self.exited_successfully = None

    @property
    def timestamps(self):
        raise Exception("Not implemented yet")
        # TODO: Given start and end date, reconstruct the timestamps
        pass

    def save(self):
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return f"<ForecastModel {self.creation_date}>"

    def launch_model(self):
        try:
            self.is_running = True
            self.save()
            self._execute_forecast()
            self.is_running = False
            self.exited_successfully = True
            self.save()
        except:
            self.is_running = False
            self.exited_successfully = False
            raise Exception("Model failed.")

    def _execute_forecast(self):
        df = (
            HistoricalData.to_df()
        )  # TODO: Should historical data be saved on the object?
        df = df.sort_values("dates")
        d = dict(df.groupby(df.dates.dt.date)["dates"].count())
        df = df[df["dates"].dt.date.apply(lambda x: d[x] == 24)]  # find all non-24

        df, tomorrow = lf.add_day(df, self.tempcs[:24])
        all_X, all_y = lf.makeUsefulDf(df, structure="3D")

        tomorrow_load, _, tomorrow_accuracy = lf.neural_net_next_day(
            all_X,
            all_y,
            epochs=self.epochs,
            save_file=self.model_path,
            model=None,
            structure="3D",
        )

        self.accuracy = tomorrow_accuracy
        self.loads = tomorrow_load
        # TODO: Confirm that this can work from any hour
        # TODO: Confirm that the zscore normalization is appropriate
        # TODO: Add tomorrow's load and accuracy to database

    @classmethod
    def data_is_prepared_for_forecast():
        pass
        df = HistoricalData.to_df()

        # check each model for data
        # TODO: reimplement data validation


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

    @classmethod
    def to_df(cls):
        return _to_df(cls)


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

    @classmethod
    def to_df(cls):
        return _to_df(cls)


def _to_df(cls):
    return pd.DataFrame(
        [
            # TODO: Rename dates to timestamp, or just make a universal var
            {"dates": row.timestamp, "load": row.load, "tempc": row.tempc}
            for row in cls.query.all()
        ]
    )


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


class User(UserMixin):
    pass
