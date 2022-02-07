import os
import datetime
import pandas as pd
from sqlalchemy import Column, Integer, Float, String, DateTime, JSON
from flask import current_app
import signal

from forecast_app.utils import db
import forecast_app.forecast as lf


class ForecastModel(db.Model):
    __tablename__ = "forecast_model"
    creation_date = Column(DateTime, primary_key=True)
    slug = Column(String, unique=True, nullable=False)
    milliseconds = Column(JSON, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    tempcs = Column(JSON, nullable=False)
    model_file = Column(String, nullable=False)
    process_file = Column(String, nullable=False)
    output_dir = Column(String, nullable=False)
    accuracy = Column(JSON)
    loads = Column(JSON)
    epochs = Column(Integer, nullable=False)

    def __init__(self):
        # NOTE: Object is initialized from state of the database
        # First ensure that the environment is prepared to create a new model
        is_prepared, self.start_date, self.end_date = self.is_prepared()
        if not is_prepared:
            raise Exception("Database is not prepared to create a model.")

        self.creation_date = datetime.datetime.utcnow()
        self.slug = str(self.creation_date.timestamp())
        self.output_dir = os.path.join(current_app.config["OUTPUT_DIR"], self.slug)
        os.mkdir(self.output_dir)

        self.model_file = os.path.join(self.output_dir, f"{self.slug}.h5")
        self.process_file = os.path.join(self.output_dir, "PID.txt")

        self.tempcs = [
            row.tempc for row in ForecastData.query.all()
        ]  # Ensure length is appropriate
        # NOTE: Cannot JSON serialize datetime objects
        # TODO: This should span start_date to end_date
        self.milliseconds = [row.milliseconds for row in ForecastData.query.all()]
        self.epochs = current_app.config["EPOCHS"]

    @property
    def timestamps(self):
        raise Exception("Not implemented yet")
        # TODO: Given start and end date, reconstruct the timestamps

    @property
    def status(self):
        # TODO: Manage strings with class variables
        # TODO: Can I just make a status property and nothing else?
        pid = self.get_process_id()
        if pid is None:
            return "Not started"
        elif pid == "COMPLETED":
            return "Finished"
        elif pid == "FAILURE" or int(pid) == signal.SIGKILL:
            return "Failed"
        else:
            return "Running"

    @property
    def is_running(self):
        return self.status == "Running"

    @property
    def exited_successfully(self):
        if self.status in ["Not started", "Running"]:
            return None
        else:
            return self.status == "Finished"

    def store_process_id(self, process_id):
        with open(self.process_file, "w") as f:
            f.write(str(process_id))

    def get_process_id(self):
        if os.path.exists(self.process_file):
            with open(self.process_file, "r") as f:
                return f.read()
        else:
            return None

    def cancel(self):
        pid = self.get_process_id()
        if self.is_running:
            os.kill(int(pid), signal.SIGKILL)
            self.store_process_id(int(signal.SIGKILL))
        else:
            raise Exception("Model is not running.")

    def save(self):
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return f"<ForecastModel {self.creation_date}>"

    def launch_model(self, app_config):
        try:
            # HACK: Because this is launched in another thread, we need to
            #       recreate the app context (!) Please think of a better way
            #       to do this.
            # https://www.reddit.com/r/flask/comments/5jrrsu/af_appapp_context_in_thread_throws_working/
            from forecast_app import create_app

            app = create_app(app_config)
            app.app_context().push()
            print("Executing forecast...")
            self._execute_forecast()
            print("Finished with forecast...")
            self.store_process_id("COMPLETED")
        except Exception as e:
            self.store_process_id("FAILURE")
            raise Exception("Model failed: {}".format(e))

    @property
    def df(self):
        df_h = HistoricalData.to_df().sort_values("dates")
        df_f = ForecastData.to_df().sort_values("dates")
        df_f = df_f[
            (self.start_date <= df_f["dates"]) & (df_f["dates"] <= self.end_date)
        ]
        return pd.concat([df_h, df_f])

    def train(self):
        pass

    def test(self):
        pass

    def _execute_forecast(self):
        df = self.df
        self.all_X, self.all_y = lf.makeUsefulDf(df)  # structure = 3D

        tomorrow_load, _, tomorrow_accuracy = lf.neural_net_next_day(
            self.all_X,
            self.all_y,
            epochs=self.epochs,
            save_file=self.model_file,
            model=None,
            # structure="3D",
        )

        self.accuracy = tomorrow_accuracy
        self.loads = tomorrow_load
        self.save()
        # TODO: Confirm that the zscore normalization is appropriate

    @classmethod
    def is_prepared(cls):
        hd_is_prepared, hd_start_date, hd_end_date = HistoricalData.is_prepared()
        fd_is_prepared, fd_start_date, fd_end_date = ForecastData.is_prepared()
        is_prepared = True if hd_is_prepared and fd_is_prepared else False
        # TODO: This doesn't seem right. Is this being tested?
        # NOTE: `is_prepared` is necessary to prevent null comparison
        if is_prepared and hd_end_date - fd_end_date > datetime.timedelta(hours=24):
            is_prepared = False

        start_date = hd_end_date + datetime.timedelta(hours=1) if is_prepared else None
        end_date = hd_end_date + datetime.timedelta(hours=24) if is_prepared else None
        return is_prepared, start_date, end_date

    # TODO: This should be at the end of launch_model
    # def done_callback(self, future):
    #     # TODO: see if future was cancelled
    #     print("Exited with Future callback")
    #     self.is_running = False
    #     self.save()


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

    @classmethod
    def is_prepared(cls):
        is_prepared = True
        df = cls.to_df().dropna()
        if df.shape[0] < 24 * 365 * 3:
            is_prepared = False
        if is_prepared:
            start_date, end_date = df.sort_values("dates")["dates"].agg(["min", "max"])
        else:
            start_date, end_date = None, None
        return is_prepared, start_date, end_date


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

    @classmethod
    def is_prepared(cls):
        df = cls.to_df()
        if df.shape[0] < 24:
            return False, None, None
        else:
            df = df.dropna(subset=["tempc"])
            start_date, end_date = df.sort_values("dates")["dates"].agg(["min", "max"])
            return True, start_date, end_date


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
    #  The columns parameter can prevent this.
    # TODO: validation should happen here
    messages = []
    LOAD_COL = current_app.config["LOAD_COL"]
    TEMP_COL = current_app.config["TEMP_COL"]
    HOUR_COL = current_app.config["HOUR_COL"]
    DATE_COL = current_app.config["DATE_COL"]

    try:
        df = pd.read_csv(filepath)

        # Some columns have spaces and quotes in their names.
        df.columns = [col.lower().strip(' "') for col in df.columns]
        df[DATE_COL] = pd.to_datetime(df[DATE_COL])

        # Hour column is in the form "HH00". This should work regardless of how
        #  the hour column is formatted.
        df[HOUR_COL] = df[HOUR_COL].astype(str).str.replace("00", "").astype(int)
        # Some hours are in a different system and go up to 24 (?!)
        if 24 in df[HOUR_COL]:
            df[HOUR_COL] -= 1

        df["timestamp"] = df.apply(
            lambda row: datetime.datetime(
                row[DATE_COL].year,
                row[DATE_COL].month,
                row[DATE_COL].day,
                row[HOUR_COL],
            ),
            axis=1,
        )

        # Ignoreing DST for now
        df.drop_duplicates(subset=["timestamp"], inplace=True)

        for column in df.columns:
            if column not in ["timestamp", LOAD_COL, TEMP_COL, HOUR_COL, DATE_COL]:
                messages.append(
                    {"level": "warning", "text": f"Column {column} not recognized."}
                )

        if columns:
            df = df[set(columns + ["timestamp"])]

        # If uploading data for the first time, don't perform tens of thousands of queries
        if cls.query.count() == 0:
            for _, row in df.iterrows():
                instance = cls(
                    timestamp=row["timestamp"],
                    load=row.get(LOAD_COL),
                    tempc=row.get(TEMP_COL),
                )
                db.session.add(instance)
            db.session.commit()
        else:
            for _, row in df.iterrows():
                instance = cls.query.get(row["timestamp"])
                if instance:
                    instance.load = row.get(LOAD_COL, instance.load)
                    instance.tempc = row.get(TEMP_COL, instance.tempc)
                else:
                    instance = cls(
                        timestamp=row["timestamp"],
                        load=row.get(LOAD_COL),
                        tempc=row.get(TEMP_COL),
                    )
                db.session.add(instance)
            db.session.commit()

        messages.append(
            {
                "level": "success",
                "text": f"Success! Loaded {len(df)} historical data points",
            }
        )
    except Exception as e:
        messages.append(
            {
                "level": "danger",
                "text": f"Failed to load data. {e}",
            }
        )
    return messages
