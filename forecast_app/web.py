from flask import Flask, render_template, url_for
import json
import pandas as pd

from utils import transform_timeseries_df_for_highcharts

app = Flask(__name__)


@app.route("/")
def login():
    return render_template("login.html", name="login")


@app.route("/load-data")
def load_data():
    df = pd.read_csv(
        "forecast_app/static/test-data/ercot-ncent-load.csv", parse_dates=["timestamp"]
    )
    table = df.to_dict("records")
    chart = transform_timeseries_df_for_highcharts(df, value="load")
    return render_template("load-data.html", name="load-data", table=table, chart=chart)


@app.route("/weather-data")
def weather_data():
    df = pd.read_csv(
        "forecast_app/static/test-data/ercot-ncent-weather.csv",
        parse_dates=["timestamp"],
    )
    table = df.to_dict("records")
    chart = transform_timeseries_df_for_highcharts(df, value="tempc")
    return render_template(
        "weather-data.html", name="weather-data", table=table, chart=chart
    )


@app.route("/forecast")
def forecast():
    return render_template("forecast.html", name="forecast")


@app.route("/instructions")
def instructions():
    return render_template("instructions.html", name="instructions")


@app.route("/model-settings")
def model_settings():
    return render_template("model-settings.html", name="model-settings")


@app.route("/user-settings")
def user_settings():
    return render_template("user-settings.html", name="user-settings")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=1546)
