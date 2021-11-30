from flask import Flask, render_template, url_for
import json
import pandas as pd

app = Flask(__name__)


@app.route("/")
def login():
    return render_template("login.html", name="login")


@app.route("/load-data")
def load_data():
    df = pd.read_csv("forecast_app/static/test-data/ercot-ncent-load.csv")
    table = df.to_dict("records")

    """
    NOTE: Chart works best using a timestamp. Getting the timestamp from a 
    dataframe is simple:
    ```
    timestamps = df['timestamp'].apply(lambda x: x.timestamp() * 1000)
    ```
    Highcharts uses milliseconds, not seconds, so multiply by 1000. And
    then zip with the load value.
    """

    with open("forecast_app/static/test-data/chart-formatted-load.json") as f:
        chart = json.load(f)
    return render_template("load-data.html", name="load-data", table=table, chart=chart)


@app.route("/weather-data")
def weather_data():
    return render_template("weather-data.html", name="weather-data")


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
