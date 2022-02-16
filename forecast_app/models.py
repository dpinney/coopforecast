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
    # TODO: This is start_datetime and end_datetime
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    tempcs = Column(JSON, nullable=False)
    model_file = Column(String, nullable=False)
    process_file = Column(String, nullable=False)
    output_dir = Column(String, nullable=False)
    accuracy = Column(JSON)
    loads = Column(JSON)
    epochs = Column(Integer, nullable=False)

    df_filename = "cached-dataframe.csv"

    def __init__(self):
        # NOTE: Object is initialized from state of the database
        # First ensure that the environment is prepared to create a new model
        is_prepared = self.is_prepared()
        self.start_date = is_prepared.get("start_date")
        self.end_date = is_prepared.get("end_date")
        if not is_prepared:
            raise Exception("Database is not prepared to create a model.")

        self.creation_date = datetime.datetime.utcnow()
        self.slug = str(self.creation_date.timestamp())
        self.output_dir = os.path.join(current_app.config["OUTPUT_DIR"], self.slug)
        os.mkdir(self.output_dir)

        self.model_file = os.path.join(self.output_dir, f"{self.slug}.h5")
        self.process_file = os.path.join(self.output_dir, "PID.txt")

        self.tempcs = [
            row.value for row in ForecastWeatherData.query.all()
        ]  # Ensure length is appropriate
        # NOTE: Cannot JSON serialize datetime objects
        # TODO: This should span start_date to end_date
        self.milliseconds = [
            (self.start_date + datetime.timedelta(hours=i)).timestamp() * 1000
            for i in range(24)
        ]
        self.epochs = current_app.config["EPOCHS"]

        self.store_df()

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

    def store_df(self):
        df_hl = HistoricalLoadData.to_df().sort_values("dates")
        df_hw = HistoricalWeatherData.to_df().sort_values("dates")
        df_h = pd.merge(df_hl, df_hw, on="dates", how="outer")

        df_f = ForecastWeatherData.to_df().sort_values("dates")
        df_f = df_f[
            (self.start_date <= df_f["dates"]) & (df_f["dates"] <= self.end_date)
        ]
        df = pd.concat([df_h, df_f])
        df.to_csv(os.path.join(self.output_dir, self.df_filename), index=False)

    @property
    def df(self):
        return pd.read_csv(os.path.join(self.output_dir, self.df_filename))

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
        hld_is_prepared = HistoricalLoadData.is_prepared()
        hwd_is_prepared = HistoricalWeatherData.is_prepared()
        fwd_is_prepared = ForecastWeatherData.is_prepared()

        if not all([hld_is_prepared, hwd_is_prepared, fwd_is_prepared]):
            return {}

        # Ensure that there are at least 24 hours of forecast data
        hd_end_date = min([hld_is_prepared["end_date"], hwd_is_prepared["end_date"]])
        if hd_end_date - fwd_is_prepared["end_date"] > datetime.timedelta(hours=24):
            return {}

        return {
            "start_date": hd_end_date + datetime.timedelta(hours=1),
            "end_date": hd_end_date + datetime.timedelta(hours=24),
        }

    # TODO: This should be at the end of launch_model
    # def done_callback(self, future):
    #     # TODO: see if future was cancelled
    #     print("Exited with Future callback")
    #     self.is_running = False
    #     self.save()


class TrainingData:
    __tablename__ = None
    friendly_name = None
    column_name = None
    timestamp = Column(DateTime, primary_key=True)
    milliseconds = Column(Integer)
    value = Column(Float)

    def __init__(self, timestamp=None, value=None):
        if pd.isna(timestamp):
            raise Exception("timestamp is a required field")
        self.timestamp = timestamp
        self.milliseconds = timestamp.timestamp() * 1000
        # NOTE: Sqlalchemy doesn't like pandas's custom NaN / NaT values.
        #  It's easiest to just cast them here.
        self.value = None if pd.isna(value) else value

    def __repr__(self):
        return f"<{self.timestamp}: {self.friendly_name} {self.value}>"

    def update_value(self, value):
        self.value = None if pd.isna(value) else value

    @classmethod
    def load_df(cls, df):
        return cls.load_data("", df=df)

    @classmethod
    def to_df(cls):
        return pd.DataFrame(
            [
                # TODO: Rename dates to timestamp, or just make a universal var
                {"dates": row.timestamp, cls.column_name: row.value}
                for row in cls.query.all()
            ]
        )

    @classmethod
    def _parse_dates(cls, df, DATE_COL, HOUR_COL):
        # TODO: Test me!
        if "timestamp" not in df.columns:
            df[DATE_COL] = pd.to_datetime(df[DATE_COL])

            # Hour column is in the form "HH00". This should work regardless of how
            #  the hour column is formatted.
            df[HOUR_COL] = df[HOUR_COL].astype(str).str.replace("00", "").astype(int)
            # Some hours are in a different system and go up to 24 (?!)
            if any(24 == df[HOUR_COL]):
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
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        # Ignoreing DST for now
        df.drop_duplicates(subset=["timestamp"], inplace=True)

        # Make datetime continuous. Don't fill with values right now.
        df = df.set_index("timestamp")
        df = df.resample("h").last()
        df["timestamp"] = df.index

        return df

    @classmethod
    def load_data(cls, filepath, df=None):
        # NOTE: Entering a csv with both weather and load will overwrite both.
        #  The columns parameter can prevent this.
        # TODO: validation should happen here
        # TODO: This is a mess.
        messages = []
        LOAD_COL = current_app.config["LOAD_COL"]
        TEMP_COL = current_app.config["TEMP_COL"]
        HOUR_COL = current_app.config["HOUR_COL"]
        DATE_COL = current_app.config["DATE_COL"]

        VAL_COL = LOAD_COL if cls.column_name == "load" else TEMP_COL

        try:
            if df is None:
                if str(filepath).endswith(".csv"):
                    df = pd.read_csv(filepath)
                elif str(filepath).endswith("xlsx"):
                    df = pd.read_excel(filepath)
                elif str(filepath) == "":
                    raise Exception("Please attach a file before uploading.")
                else:
                    raise Exception("File extension not recognized.")

            # Some columns have spaces and quotes in their names.
            df.columns = [col.lower().strip(' "') for col in df.columns]

            df = cls._parse_dates(df, DATE_COL, HOUR_COL)

            for column in df.columns:
                if column not in ["timestamp", VAL_COL, HOUR_COL, DATE_COL]:
                    messages.append(
                        {
                            "level": "warning",
                            "text": f'Warning: column "{column}" will not be imported.',
                        }
                    )

            # Select only the columns relevant for this class
            df = df[[VAL_COL, "timestamp"]]

            # If uploading data for the first time, don't perform tens of thousands of queries
            if cls.query.count() == 0:
                for _, row in df.iterrows():
                    instance = cls(
                        timestamp=row["timestamp"],
                        value=row.get(VAL_COL),
                    )
                    db.session.add(instance)
                db.session.commit()
            else:
                for _, row in df.iterrows():
                    instance = cls.query.get(row["timestamp"])
                    if instance:
                        instance.update_value(row.get(VAL_COL, instance.value))
                    else:
                        instance = cls(
                            timestamp=row["timestamp"],
                            value=row.get(VAL_COL),
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
            # TODO: Add this logic to all try/excepts
            if current_app.config["DEBUG"]:
                raise e
        return messages


class ForecastWeatherData(TrainingData, db.Model):
    __tablename__ = "forecast_weather_data"
    friendly_name = "Forecast Temperature"
    column_name = "tempc"

    @classmethod
    def is_prepared(cls):
        df = cls.to_df()
        if df.shape[0] < 24:
            return {}

        df = df.dropna(subset=["tempc"])
        start_date, end_date = df.sort_values("dates")["dates"].agg(["min", "max"])
        return {
            "start_date": start_date,
            "end_date": end_date,
        }


class HistoricalWeatherData(TrainingData, db.Model):
    __tablename__ = "historical_weather_data"
    friendly_name = "Historical Temperature"
    column_name = "tempc"

    @classmethod
    def is_prepared(cls):
        df = cls.to_df().dropna()
        if df.shape[0] < 24 * 365 * 3:
            return {}

        start_date, end_date = df.sort_values("dates")["dates"].agg(["min", "max"])
        return {
            "start_date": start_date,
            "end_date": end_date,
        }


class HistoricalLoadData(TrainingData, db.Model):
    __tablename__ = "historical_load_data"
    friendly_name = "Historical Load"
    column_name = "load"

    @classmethod
    def is_prepared(cls):
        df = cls.to_df().dropna()
        if df.shape[0] < 24 * 365 * 3:
            return {}
        start_date, end_date = df.sort_values("dates")["dates"].agg(["min", "max"])
        return {
            "start_date": start_date,
            "end_date": end_date,
        }
