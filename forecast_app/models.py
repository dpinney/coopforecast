"""A collection of ORMs for the forecast_app, configured with sqlalchemy."""

import os
import datetime
import pandas as pd
from sqlalchemy import Column, Integer, Float, String, DateTime, JSON
from flask import current_app
import signal
import tensorflow as tf

from forecast_app.utils import db, safe_flash
import forecast_app.forecast as lf


class ForecastModel(db.Model):
    """A database model that stores information about a deep learning model"""

    __tablename__ = "forecast_model"
    creation_date = Column(DateTime, primary_key=True)
    slug = Column(String, unique=True, nullable=False)
    milliseconds = Column(JSON, nullable=False)  # TODO: This should be a property
    # TODO: This is start_dt and end_dt
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    tempcs = Column(JSON, nullable=False)  # TODO: Remove me, this is tracked in the df
    model_file = Column(String, nullable=False)  # TODO: Remove me
    process_file = Column(String, nullable=False)  # TODO: Remove me
    output_dir = Column(String, nullable=False)
    accuracy = Column(JSON)
    loads = Column(JSON)  # TODO: Remove me, this is tracked in the df
    epochs = Column(Integer, nullable=False)

    df_filename = "cached-dataframe.csv"

    def __init__(self):
        """Collect the current state of the database and prepare a model for training."""

        # NOTE: Object is initialized from state of the database
        # First ensure that the environment is prepared to create a new model
        is_prepared = self.is_prepared()
        self.start_date = is_prepared.get("start_date")
        self.end_date = is_prepared.get("end_date")
        if not is_prepared:
            raise Exception("Database is not prepared to create a model.")

        self.creation_date = datetime.datetime.now()
        self.slug = self.creation_date.strftime("%Y-%m-%d.%H-%M-%S")
        self.output_dir = os.path.join(current_app.config["OUTPUT_DIR"], self.slug)
        os.makedirs(self.output_dir)

        # TODO: This should be named path or rewrite this
        # TODO: These should be removed from the database and set as properties
        self.model_file = os.path.join(self.output_dir, self.model_filename)
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

        df = self.collect_training_data()
        self.store_df(df)

    @property
    def model_filename(self):
        """Return the filename of the model."""
        # TODO: This can be a friendlier name, it's nested in the output_dir
        return f"{self.slug}.h5"

    @property
    def status(self):
        """Return the status of the model, either "Not started", "Finished", "Failed", or "Running"."""
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
        """Return True if the model is currently running."""
        return self.status == "Running"

    @property
    def exited_successfully(self):
        """Return True if the model exited successfully."""

        if self.status in ["Not started", "Running"]:
            return None
        else:
            return self.status == "Finished"

    def store_process_id(self, process_id):
        """Store the process id of the model in a text file to help with multiprocessing."""

        with open(self.process_file, "w") as f:
            f.write(str(process_id))

    def get_process_id(self):
        """Extract the process id from the process file to help with multiprocessing."""

        if os.path.exists(self.process_file):
            with open(self.process_file, "r") as f:
                return f.read()
        else:
            return None

    def cancel(self):
        """Cancel the model's training if it is running. If it isn't running, raise an exception."""

        pid = self.get_process_id()
        if self.is_running:
            os.kill(int(pid), signal.SIGKILL)
            self.store_process_id(int(signal.SIGKILL))
        else:
            raise Exception("Model is not running.")

    def save(self):
        """Save the model's state to the database. WARNING: Other queued changes will also be committed."""

        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return f"<ForecastModel {self.creation_date}>"

    def launch_model(self, app_config):
        """Launch the model's training in a separate process."""

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
            raise Exception(f"Model failed: {e}")

    def collect_training_data(self):
        """Save the state of the database into a dataframe that is in the correct format for training.

        Null values are filled in, and other data cleaning takes place, but full
        df exploding is not performed.
        """

        df_hl = HistoricalLoadData.to_df().sort_values("dates")
        df_hw = HistoricalWeatherData.to_df().sort_values("dates")

        # Get the intersection of the two dataframes, and then resample hourly
        #  to make a continuous datetime index.
        df_h = pd.merge(df_hl, df_hw, on="dates", how="inner")
        df_h = df_h.set_index("dates", drop=False)
        df_h = df_h.resample("h").ffill()

        # Fill Nans for training data
        # TODO: Have configuration to set the maximum number of missing values filled
        #  this is configured via the pandas "limit" parameter
        # TODO: This would ideally be replaced with interpolation
        df_h = df_h.fillna(method="ffill").fillna(method="bfill")

        df_f = ForecastWeatherData.to_df().sort_values("dates")
        df_f = df_f[
            (self.start_date <= df_f["dates"]) & (df_f["dates"] <= self.end_date)
        ]

        # TODO: Allow for different sized days
        # Remove all days that are not the same size
        df = pd.concat([df_h, df_f])
        d = dict(df.groupby(df.dates.dt.date)["dates"].count())
        df = df[df["dates"].dt.date.apply(lambda x: d[x] == 24)]
        return df

    @property
    def df_path(self):
        """Path to the key dataframe used for training."""
        return os.path.join(self.output_dir, self.df_filename)

    def store_df(self, df):
        """Store the dataframe in the output directory."""
        df.to_csv(self.df_path, index=False)

    def get_df(self):
        """Return the dataframe used for training."""
        return pd.read_csv(self.df_path, parse_dates=["dates"])

    def get_model(self):
        """Return the model."""
        # TODO: Raise an exception if the model doesn't exist
        return tf.keras.models.load_model(self.model_file)

    def _execute_forecast(self):
        """Execute the forecast (outside a thread.) And save all info after finishing.

        Given the cached dataframe collected from the database's state when the
        object was initialized, generate the exploded, normalized dataframe, split
        into training and testing sets, and train the model. Store all pertinent
        information in the database.
        """
        # TODO: Separate this into three functions for easier testing.

        df = self.get_df()
        self.all_X, self.all_y = lf.generate_x_and_ys(df)

        tomorrow_load, model, tomorrow_accuracy = lf.train_and_forecast_next_day(
            self.all_X,
            self.all_y,
            epochs=self.epochs,
            save_file=self.model_file,
        )

        # HACK: Set forecasted load on cached dataframe
        df["forecasted_load"] = model.predict(self.all_X.values.tolist())
        self.store_df(df)

        self.accuracy = tomorrow_accuracy
        self.loads = tomorrow_load
        self.save()

    @classmethod
    def is_prepared(cls):
        """Return the start and end timestamps of when the current database can forecast."""

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


class TrainingData:
    """Abstract class for different types of data needed to make a forecast."""

    __tablename__ = None
    friendly_name = None
    column_name = None
    timestamp = Column(DateTime, primary_key=True)
    milliseconds = Column(Integer)
    value = Column(Float)

    def __init__(self, timestamp=None, value=None):
        """Initialize the object with a timestamp and a value and generate remaining attributes."""

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
        """Safely update the value of the object."""
        # TODO: Implement privacy so that users can't update the value of the object
        #  https://stackoverflow.com/questions/10929004/how-to-restrict-setting-an-attribute-outside-of-constructor
        self.value = None if pd.isna(value) else value

    @classmethod
    def load_df(cls, df):
        """Load a dataframe into the database."""
        return cls.load_data("", df=df)

    @classmethod
    def to_df(cls):
        """Return a dataframe of the data in the database in the format used across the app."""

        return pd.DataFrame(
            [
                # TODO: Rename dates to timestamp, or just make a universal var
                {"dates": row.timestamp, cls.column_name: row.value}
                for row in cls.query.all()
            ]
        )

    @classmethod
    def _parse_dates(cls, df, DATE_COL, HOUR_COL):
        """Parse an incoming dataframe's columns to correctly format the timestamps into the app's required format."""

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
    def is_prepared(cls):
        """Return the start and end dates of the data if it is prepared. Return an empty dict otherwise.

        A model is prepared if there is there are at least `minimum_data_required` values in the database.
        """
        df = cls.to_df()
        if df.empty:
            return {}

        df = df.dropna(subset=[cls.column_name])
        if df.shape[0] < cls.minimum_data_required:
            return {}

        start_date, end_date = df.sort_values("dates")["dates"].agg(["min", "max"])
        return {
            "start_date": start_date,
            "end_date": end_date,
        }

    @classmethod
    def load_data(cls, filepath, df=None):
        """Given a filepath or a dataframe, parse the data and load it into the database of the given model."""

        # NOTE: Entering a csv with both weather and load will overwrite both.
        #  The columns parameter can prevent this.
        # TODO: validation should happen here
        # TODO: This is a mess. Separate out into different functions for easier testing.
        LOAD_COL = current_app.config["LOAD_COL"]
        TEMP_COL = current_app.config["TEMP_COL"]
        HOUR_COL = current_app.config["HOUR_COL"]
        DATE_COL = current_app.config["DATE_COL"]

        # TODO: Make a more immutable way of determining the value column
        VAL_COL = LOAD_COL if cls.column_name == "load" else TEMP_COL

        try:
            if df is None:
                if str(filepath).endswith(".csv"):
                    df = pd.read_csv(filepath)
                elif str(filepath).endswith("xlsx"):
                    df = pd.read_excel(filepath)
                elif str(filepath) == "":
                    safe_flash("Please attach a file before uploading.", "danger")
                else:
                    safe_flash("File extension not recognized.", "danger")

            # Some columns have spaces and quotes in their names.
            df.columns = [col.lower().strip(' "') for col in df.columns]

            df = cls._parse_dates(df, DATE_COL, HOUR_COL)

            for column in df.columns:
                if column not in ["timestamp", VAL_COL, HOUR_COL, DATE_COL]:
                    safe_flash(
                        f'Warning: column "{column}" will not be imported.', "warning"
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

            safe_flash(f"Success! Loaded {len(df)} historical data points", "success")

        except Exception as e:
            safe_flash("Error: failed to load data. " + str(e), "danger")


class ForecastWeatherData(TrainingData, db.Model):
    """Table of forecasted weather data."""

    __tablename__ = "forecast_weather_data"
    friendly_name = "Forecast Temperature"
    column_name = "tempc"
    minimum_data_required = 24


class HistoricalWeatherData(TrainingData, db.Model):
    """Table of historical weather data."""

    __tablename__ = "historical_weather_data"
    friendly_name = "Historical Temperature"
    column_name = "tempc"
    minimum_data_required = 24 * 365 * 3


class HistoricalLoadData(TrainingData, db.Model):
    """Table of historical load data."""

    __tablename__ = "historical_load_data"
    friendly_name = "Historical Load"
    column_name = "load"
    minimum_data_required = 24 * 365 * 3
