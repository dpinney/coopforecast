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


def _data_transform_3d(data, timesteps=24, var="x"):
    # TODO: make this clearer
    m = []
    s = data.to_numpy()
    for i in range(s.shape[0] - timesteps):
        m.append(s[i : i + timesteps].tolist())

    if var == "x":
        t = np.zeros((len(m), len(m[0]), len(m[0][0])))
        for i, x in enumerate(m):
            for j, y in enumerate(x):
                for k, z in enumerate(y):
                    t[i, j, k] = z
    else:
        t = np.zeros((len(m), len(m[0])))
        for i, x in enumerate(m):
            for j, y in enumerate(x):
                t[i, j] = y
    return t


def generate_exploded_df(df, noise=2.5, hours_prior=24):
    """Turn a dataframe of datetime and load data into a dataframe useful for machine learning.

    Normalize values, expload categorical data, and add noise to the temperature data to simulate
    uncertainty in a forecast.
    """

    # TODO: Instead of shifting by hours prior, values should be explicitly grabbed by datetime.
    # TODO: Forecast from any hour not just the first hour of the day
    # TODO: Sort the dataframe by datetime.

    DT_COL = "dates"
    LOAD_COL = "load"

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

    return _data_transform_3d(r_df, var="x"), _data_transform_3d(df["load"], var="y")


class DataSplit:
    """A class to make the data split consistent across all operations."""

    def __init__(self, all_X, all_y, train_size=0.8, hours_prior=24, LOAD_COL="load"):
        """Initialize the data split."""

        self.all_X, self.all_y = all_X, all_y

        # TODO: Use last valid index to get the training data.
        self.test_train_X, self.test_train_y = (
            self.all_X[:-hours_prior],
            self.all_y[:-hours_prior],
        )

        self.train_X, self.test_X, self.train_y, self.test_y = train_test_split(
            self.test_train_X, self.test_train_y, train_size=train_size
        )


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
            layers.Dense(ds.train_X.shape[2] * HOURS_AHEAD // 2, activation=tf.nn.relu),
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


def load_predictions_to_df(df, model, ds: DataSplit):
    """Load the predictions from the model into a dataframe."""
    df = df.set_index("dates", drop=False)
    pred_df = pd.DataFrame(
        model.predict(ds.all_X),
        columns=[f"load_in_{hour+1}_hours" for hour in range(24)],
        index=df.index[:-24],
    )
    df = pd.concat([df, pred_df], axis=1)
    return df
