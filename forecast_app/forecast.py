"""A collection of utilities to help with building and executing the machine learning model."""

import datetime
import os
import pickle
from datetime import date
from datetime import datetime as dt
from datetime import timedelta
from os.path import join as pJoin

import numpy as np
import pandas as pd
import tensorflow as tf
from scipy.stats import zscore
from sklearn.model_selection import train_test_split
from tensorflow.keras import layers


class DataSplit:
    """A class to make the data split consistent across all operations."""

    def __init__(
        self, df, train_size=0.8, hours_prior=24, load_col="load", dt_col="dates"
    ):
        """Initialize the data split."""
        self.df = df
        self.hours_prior = hours_prior
        self.load_col = load_col
        self.dt_col = dt_col

        self.generate_exploded_data()

        # TODO: Use last valid index to get the training data.
        self.test_train_X, self.test_train_y = (
            self.all_X[:-hours_prior],
            self.all_y[:-hours_prior],
        )

        self.train_X, self.test_X, self.train_y, self.test_y = train_test_split(
            self.test_train_X, self.test_train_y, train_size=train_size
        )

    def generate_exploded_data(self, noise=2.5):
        """Turn a dataframe of datetime and load data into a dataframe useful for machine learning.

        Normalize values, expload categorical data, and add noise to the temperature data to simulate
        uncertainty in a forecast.
        """

        # TODO: Instead of shifting by hours prior, values should be explicitly grabbed by datetime.
        # TODO: Forecast from any hour not just the first hour of the day
        # TODO: Sort the dataframe by datetime.

        DT_COL = self.dt_col
        LOAD_COL = self.load_col
        hours_prior = self.hours_prior
        df = self.df

        df["year"] = df[DT_COL].dt.year
        df["month"] = df[DT_COL].dt.month
        df["day"] = df[DT_COL].dt.day

        r_df = pd.DataFrame()

        # LOAD
        r_df["load_n"] = df[LOAD_COL] / (df[LOAD_COL].max() - df[LOAD_COL].min())
        # NOTE: This requires a sorted, continuous dataframe!
        r_df["load_prev_n"] = r_df["load_n"].shift(hours_prior)
        r_df["load_prev_n"].bfill(inplace=True)

        # Remove normalized load from Xs, otherwise you're just feeding the answers into the model.
        r_df.drop(["load_n"], axis=1, inplace=True)

        # DATE
        # NOTE: zscore will be all nans if any are nans!
        r_df["years_n"] = zscore(df[DT_COL].dt.year)
        r_df = pd.concat(
            [
                r_df,
                pd.get_dummies(df.dates.dt.hour, prefix="hour"),
                pd.get_dummies(df.dates.dt.dayofweek, prefix="day"),
                pd.get_dummies(df.dates.dt.month, prefix="month"),
            ],
            axis=1,
        )

        # TEMP
        temp_noise = df["tempc"] + np.random.normal(0, noise, df.shape[0])
        r_df["temp_n"] = zscore(temp_noise)
        r_df["temp_n^2"] = zscore([x * x for x in temp_noise])

        # Set the dataframe for training and testing.
        self.all_X = self._data_transform_3d(r_df)
        self.all_y = self._data_transform_3d(df[LOAD_COL])

        feature_count = r_df.shape[1]
        # The important predictions of the model are those that start at the hour we care about.
        #  Because we're cutting off the input df at the model.end_date, this should be evenly
        #  divisible by 24.
        # TODO: Double check that the start_date is equal to the model's starting hour.
        self.important_X = r_df.to_numpy().reshape((-1, hours_prior, feature_count))

    @staticmethod
    def _data_transform_3d(data, timesteps=24):
        """Group the data into a 24-day 3D array.

        The input dimensions are [number of tests, features] and we need  [number of tests, timestamps, features].
        """
        return_l = []
        np_a = data.to_numpy()
        for i in range(np_a.shape[0] - timesteps):
            return_l.append(np_a[i : i + timesteps])
        return np.array(return_l)


def train_and_test_model(ds: DataSplit, epochs=20, save_file=None):
    """Train a neural net and forecast the next day's load."""
    HOURS_AHEAD = 24

    model = tf.keras.Sequential(
        [
            layers.Dense(
                ds.train_X.shape[2],
                activation=tf.nn.relu,
                input_shape=(HOURS_AHEAD, ds.train_X.shape[2]),
            ),
            layers.Dense(ds.train_X.shape[2], activation=tf.nn.relu),
            layers.Dense(ds.train_X.shape[2], activation=tf.nn.relu),
            layers.Dense(ds.train_X.shape[2], activation=tf.nn.relu),
            layers.Dense(ds.train_X.shape[2], activation=tf.nn.relu),
            layers.Flatten(),
            layers.Dense(ds.train_X.shape[2] * HOURS_AHEAD, activation=tf.nn.relu),
            layers.Dense(ds.train_X.shape[2] * HOURS_AHEAD // 2, activation=tf.nn.relu),
            layers.Dense(ds.train_X.shape[2] * HOURS_AHEAD // 4, activation=tf.nn.relu),
            layers.Dense(HOURS_AHEAD),
        ]
    )

    nadam = tf.keras.optimizers.Nadam(learning_rate=0.002, beta_1=0.9, beta_2=0.999)
    model.compile(optimizer=nadam, loss="mape")
    model.fit(ds.train_X, ds.train_y, epochs=epochs)

    accuracy = {
        "train": model.evaluate(ds.train_X, ds.train_y, verbose=0),
        "test": model.evaluate(ds.test_X, ds.test_y, verbose=0),
    }

    if save_file != None:
        model.save(save_file)

    return model, accuracy


# def get_forecasted_load(df, model, ds: DataSplit):
#     """Load the predictions from the model into a dataframe."""
#     df = df.set_index("dates", drop=False)
#     breakpoint()
#     pred_df = pd.DataFrame(
#         model.predict(ds.all_X),
#         columns=[f"load_in_{hour+1}_hours" for hour in range(24)],
#         index=df.index[:-24],
#     )
#     df = pd.concat([df, pred_df], axis=1)
