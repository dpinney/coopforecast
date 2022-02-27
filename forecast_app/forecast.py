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


def generate_x_and_ys(df, noise=2.5, hours_prior=24):
    """Turn a dataframe of datetime and load data into a dataframe useful for machine learning.

    Normalize values, expload categorical data, and add noise to the temperature data to simulate
    uncertainty in a forecast.
    """

    # TODO: Instead of shifting by hours prior, values should be explicitly grabbed by datetime.

    def _isHoliday(holiday, df):
        # TODO: Search for libraries that do this for you.
        m1 = None
        if holiday == "New Year's Day":
            m1 = (df["dates"].dt.month == 1) & (df["dates"].dt.day == 1)
        if holiday == "Independence Day":
            m1 = (df["dates"].dt.month == 7) & (df["dates"].dt.day == 4)
        if holiday == "Christmas Day":
            m1 = (df["dates"].dt.month == 12) & (df["dates"].dt.day == 25)
        m1 = df["dates"].dt.date.isin(nerc6[holiday]) if m1 is None else m1
        m2 = df["dates"].dt.date.isin(nerc6.get(holiday + " (Observed)", []))
        return m1 | m2

    with open("forecast_app/static/holidays.pickle", "rb") as f:
        nerc6 = pickle.load(
            f, encoding="latin_1"
        )  # Is this the right codec? It might be cp1252

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

    for holiday in [
        "New Year's Day",
        "Memorial Day",
        "Independence Day",
        "Labor Day",
        "Thanksgiving",
        "Christmas Day",
    ]:
        r_df[holiday] = _isHoliday(holiday, df)

    # TEMP
    temp_noise = df["tempc"] + np.random.normal(0, noise, df.shape[0])
    r_df["temp_n"] = zscore(temp_noise)
    r_df["temp_n^2"] = zscore([x * x for x in temp_noise])

    return r_df, df["load"]


def MAPE(predictions, answers):
    """Calculate the mean absolute percentage error."""

    assert len(predictions) == len(answers)
    return (
        sum([abs(x - y) / (y + 1e-5) for x, y in zip(predictions, answers)])
        / len(answers)
        * 100
    )


def train_neural_net(X_train, y_train, epochs):
    """Train a new neural net given training data the number of epochs."""

    model = tf.keras.Sequential(
        [
            layers.Dense(
                X_train.shape[1],
                activation=tf.nn.relu,
                input_shape=[len(X_train.keys())],
            ),
            layers.Dense(X_train.shape[1], activation=tf.nn.relu),
            layers.Dense(X_train.shape[1], activation=tf.nn.relu),
            layers.Dense(X_train.shape[1], activation=tf.nn.relu),
            layers.Dense(X_train.shape[1], activation=tf.nn.relu),
            layers.Dense(1),
        ]
    )

    nadam = tf.keras.optimizers.Nadam(learning_rate=0.002, beta_1=0.9, beta_2=0.999)
    model.compile(optimizer=nadam, loss="mape")

    x, y = np.asarray(X_train.values.tolist()), np.asarray(y_train.tolist())
    model.fit(x, y, epochs=epochs)

    return model


def train_and_forecast(all_X, all_y, epochs=20, save_file=None, hours_prior=24):
    """Train a neural net and forecast the next day's load."""
    all_X_n, all_y_n = all_X[:-hours_prior], all_y[:-hours_prior]
    X_train = all_X_n[:-8760]
    y_train = all_y_n[:-8760]
    X_test = all_X_n[-8760:]
    y_test = all_y_n[-8760:]

    model = train_neural_net(X_train, y_train, epochs)

    predictions_test = [
        float(f) for f in model.predict(np.asarray(X_test.values.tolist()), verbose=0)
    ]
    train = [
        float(f) for f in model.predict(np.asarray(X_train.values.tolist()), verbose=0)
    ]
    accuracy = {
        "test": MAPE(predictions_test, y_test),
        "train": MAPE(train, y_train),
    }
    predictions = [
        float(f)
        for f in model.predict(
            np.asarray(all_X[-hours_prior:].values.tolist()), verbose=0
        )
    ]

    if save_file != None:
        model.save(save_file)

    return predictions, model, accuracy
