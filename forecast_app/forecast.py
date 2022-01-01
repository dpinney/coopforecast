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


def makeUsefulDf(df, noise=2.5, hours_prior=24, structure=None):
    """
    Turn a dataframe of datetime and load data into a dataframe useful for
    machine learning. Normalize values.
    """

    def _isHoliday(holiday, df):
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

    def _data_transform_3d(data, timesteps=24, var="x"):
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

    # TODO: Allow for different sized days
    d = dict(df.groupby(df.dates.dt.date)["dates"].count())
    df = df[df["dates"].dt.date.apply(lambda x: d[x] == 24)]

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
    r_df["load_prev_n"] = r_df["load_n"].shift(hours_prior)
    r_df["load_prev_n"].bfill(inplace=True)

    if structure != "3D":

        def _chunks(l, n):
            return [l[i : i + n] for i in range(0, len(l), n)]

        n = np.array(
            [val for val in _chunks(list(r_df["load_n"]), 24) for _ in range(24)]
        )
        l = ["l" + str(i) for i in range(24)]
        for i, s in enumerate(l):
            r_df[s] = n[:, i]
            r_df[s] = r_df[s].shift(hours_prior)
            r_df[s] = r_df[s].bfill()

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

    return (
        (r_df, df["load"])
        if structure != "3D"
        else (
            _data_transform_3d(r_df, var="x"),
            _data_transform_3d(df["load"], var="y"),
        )
    )


def MAPE(predictions, answers):
    assert len(predictions) == len(answers)
    return (
        sum([abs(x - y) / (y + 1e-5) for x, y in zip(predictions, answers)])
        / len(answers)
        * 100
    )


def train_neural_net(X_train, y_train, epochs, HOURS_AHEAD=24, structure=None):
    if structure != "3D":
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
    else:
        model = tf.keras.Sequential(
            [
                layers.Dense(
                    X_train.shape[2],
                    activation=tf.nn.relu,
                    input_shape=(HOURS_AHEAD, X_train.shape[2]),
                ),
                layers.Dense(X_train.shape[2], activation=tf.nn.relu),
                layers.Dense(X_train.shape[2], activation=tf.nn.relu),
                layers.Dense(X_train.shape[2], activation=tf.nn.relu),
                layers.Dense(X_train.shape[2], activation=tf.nn.relu),
                layers.Flatten(),
                layers.Dense(
                    X_train.shape[2] * HOURS_AHEAD // 2, activation=tf.nn.relu
                ),
                layers.Dense(HOURS_AHEAD),
            ]
        )

    nadam = tf.keras.optimizers.Nadam(learning_rate=0.002, beta_1=0.9, beta_2=0.999)
    model.compile(optimizer=nadam, loss="mape")

    x, y = (
        (np.asarray(X_train.values.tolist()), np.asarray(y_train.tolist()))
        if structure != "3D"
        else (X_train, y_train)
    )
    model.fit(x, y, epochs=epochs)

    return model


def neural_net_predictions(all_X, all_y, epochs=20, model=None, save_file=None):
    X_train, y_train = all_X[:-8760], all_y[:-8760]

    if model == None:
        model = train_neural_net(X_train, y_train, epochs)

    predictions = [
        float(f) for f in model.predict(np.asarray(all_X[-8760:].values.tolist()))
    ]
    train = [float(f) for f in model.predict(np.asarray(all_X[:-8760].values.tolist()))]
    accuracy = {
        "test": MAPE(predictions, all_y[-8760:]),
        "train": MAPE(train, all_y[:-8760]),
    }

    if save_file != None:
        model.save(save_file)

    return [
        float(f) for f in model.predict(np.asarray(all_X[-8760:].values.tolist()))
    ], accuracy


def neural_net_next_day(
    all_X, all_y, epochs=20, hours_prior=24, save_file=None, model=None, structure=None
):
    all_X_n, all_y_n = all_X[:-hours_prior], all_y[:-hours_prior]
    X_train = all_X_n[:-8760]
    y_train = all_y_n[:-8760]
    X_test = all_X_n[-8760:]
    y_test = all_y_n[-8760:]

    if model == None:
        model = train_neural_net(X_train, y_train, epochs, structure=structure)

    if structure != "3D":
        predictions_test = [
            float(f)
            for f in model.predict(np.asarray(X_test.values.tolist()), verbose=0)
        ]
        train = [
            float(f)
            for f in model.predict(np.asarray(X_train.values.tolist()), verbose=0)
        ]
        accuracy = {
            "test": MAPE(predictions_test, y_test),
            "train": MAPE(train, y_train),
        }
        predictions = [
            float(f)
            for f in model.predict(np.asarray(all_X[-24:].values.tolist()), verbose=0)
        ]
    else:
        accuracy = {
            "test": model.evaluate(X_test, y_test),
            "train": model.evaluate(X_train, y_train),
        }
        predictions = [
            float(f) for f in model.predict(np.array([all_X[-1]]), verbose=0)[0]
        ]

    if save_file != None:
        model.save(save_file)

    return predictions, model, accuracy


def add_day(df, weather):
    lr = df.iloc[-1]
    if "dates" in df.columns:
        last_day = lr.dates
        df.drop(["dates"], axis=1, inplace=True)  # TODO: WHY?!
    else:
        last_day = date(int(lr.year), int(lr.month), int(lr.day))
    predicted_day = last_day + datetime.timedelta(days=1)

    d_24 = [
        {
            "load": -999999,
            "tempc": w,
            "year": predicted_day.year,
            "month": predicted_day.month,
            "day": predicted_day.day,
            "hour": i,
        }
        for i, w in enumerate(weather)
    ]

    df = df.append(d_24, ignore_index=True)

    return df, predicted_day
