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
from tensorflow.keras import layers


def generate_exploded_df(df, noise=2.5, hours_prior=24):
    """Turn a dataframe of datetime and load data into a dataframe useful for machine learning.

    Normalize values, expload categorical data, and add noise to the temperature data to simulate
    uncertainty in a forecast.
    """

    # TODO: Instead of shifting by hours prior, values should be explicitly grabbed by datetime.
    # TODO: Forecast from any hour not just the first hour of the day
    # TODO: Sort the dataframe by datetime.

    # def get_previous_days_load(row, hour, col):
    #     day_before = row.name.date - timedelta(days=1)
    #     return r_df.loc[day_before.replace(hour=hour)][col]

    DT_COL = "dates"
    LOAD_COL = "load"
    # breakpoint()

    df["year"] = df[DT_COL].dt.year
    df["month"] = df[DT_COL].dt.month
    df["day"] = df[DT_COL].dt.day

    r_df = pd.DataFrame()

    # LOAD
    r_df["load_n"] = df[LOAD_COL] / (df[LOAD_COL].max() - df[LOAD_COL].min())
    # NOTE: This requires a sorted, continuous dataframe!
    r_df["load_prev_n"] = r_df["load_n"].shift(hours_prior)
    r_df["load_prev_n"].bfill(inplace=True)

    def _chunks(l, n):
        return [l[i : i + n] for i in range(0, len(l), n)]

    n = np.array([val for val in _chunks(list(r_df["load_n"]), 24) for _ in range(24)])
    l = ["l" + str(i) for i in range(24)]
    for i, s in enumerate(l):
        r_df[s] = n[:, i]
        r_df[s] = r_df[s].shift(hours_prior)
        r_df[s] = r_df[s].bfill()

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

    # Append the y mapping to the dataframe
    r_df[LOAD_COL] = df[LOAD_COL]

    return r_df


class DataSplit:
    """A class to make the data split consistent across all operations."""

    def __init__(self, df, train_size=0.8, hours_prior=24, LOAD_COL="load"):
        """Initialize the data split."""

        self.df = df.copy()
        self.all_X, self.all_y = (
            df.drop([LOAD_COL], axis=1),
            df[LOAD_COL],
        )

        # TODO: Use last valid index to get the training data.
        self.test_train_X, self.test_train_y = (
            self.all_X[:-hours_prior],
            self.all_y[:-hours_prior],
        )
        self.train_X = self.test_train_X.sample(frac=train_size)
        self.test_X = self.test_train_X.drop(self.train_X.index)
        self.train_y = self.test_train_y[self.train_X.index]
        self.test_y = self.test_train_y[self.test_X.index]


def train_and_test_model(ds: DataSplit, epochs=20, save_file=None):
    """Train a neural net and forecast the next day's load."""

    model = tf.keras.Sequential(
        [
            layers.Dense(
                ds.train_X.shape[1],
                activation=tf.nn.relu,
                input_shape=[len(ds.train_X.keys())],
            ),
            layers.Dense(ds.train_X.shape[1], activation=tf.nn.relu),
            layers.Dense(ds.train_X.shape[1], activation=tf.nn.relu),
            layers.Dense(ds.train_X.shape[1], activation=tf.nn.relu),
            layers.Dense(ds.train_X.shape[1], activation=tf.nn.relu),
            layers.Dense(1),
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
