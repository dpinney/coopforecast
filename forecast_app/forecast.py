"""A collection of utilities to help with building and executing the machine learning model."""

import numpy as np
import pandas as pd
import os
from os.path import join as pJoin
import datetime
from datetime import datetime as dt
from datetime import timedelta, date
import pickle
from scipy.stats import zscore

import tensorflow as tf
from tensorflow.keras import layers


def generate_exploded_df(df, noise=2.5, hours_prior=24):
    """Turn a dataframe of datetime and load data into a dataframe useful for machine learning.

    Normalize values, expload categorical data, and add noise to the temperature data to simulate
    uncertainty in a forecast.
    """

    # TODO: Instead of shifting by hours prior, values should be explicitly grabbed by datetime.

    df["year"] = df["dates"].dt.year
    df["month"] = df["dates"].dt.month
    df["day"] = df["dates"].dt.day

    r_df = pd.DataFrame()

    # LOAD
    r_df["load_n"] = df["load"] / (df["load"].max() - df["load"].min())
    # NOTE: This requires a continuous dataframe!
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
    r_df["years_n"] = zscore(df["dates"].dt.year)
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
    r_df["load"] = df["load"]

    return r_df


def split_data(exploded_df, train_size=0.8, hours_prior=24):
    """document me!"""
    # TODO: Make into a class / named tuple?
    all_X, all_y = exploded_df.drop(["load"], axis=1), exploded_df["load"]

    # TODO: Use last valid index to get the training data.
    all_X_n, all_y_n = all_X[:-hours_prior], all_y[:-hours_prior]
    train_X = all_X_n.sample(frac=train_size)
    test_X = all_X_n.drop(train_X.index)
    train_y = all_y_n[train_X.index]
    test_y = all_y_n[test_X.index]

    return {
        "train_X": train_X,
        "train_y": train_y,
        "test_X": test_X,
        "test_y": test_y,
        # NOTE: `all_X` includes the Xs of the next day.
        "all_X": all_X,
    }


def train_and_test_model(split_data, epochs=20, save_file=None):
    """Train a neural net and forecast the next day's load."""

    train_X, train_y, test_X, test_y = (
        split_data["train_X"],
        split_data["train_y"],
        split_data["test_X"],
        split_data["test_y"],
    )

    model = tf.keras.Sequential(
        [
            layers.Dense(
                train_X.shape[1],
                activation=tf.nn.relu,
                input_shape=[len(train_X.keys())],
            ),
            layers.Dense(train_X.shape[1], activation=tf.nn.relu),
            layers.Dense(train_X.shape[1], activation=tf.nn.relu),
            layers.Dense(train_X.shape[1], activation=tf.nn.relu),
            layers.Dense(train_X.shape[1], activation=tf.nn.relu),
            layers.Dense(1),
        ]
    )

    nadam = tf.keras.optimizers.Nadam(learning_rate=0.002, beta_1=0.9, beta_2=0.999)
    model.compile(optimizer=nadam, loss="mape")
    model.fit(train_X, train_y, epochs=epochs)

    accuracy = {
        "test": model.evaluate(split_data["test_X"], split_data["test_y"]),
        "train": model.evaluate(split_data["train_X"], split_data["train_y"]),
    }

    if save_file != None:
        model.save(save_file)

    return model, accuracy
