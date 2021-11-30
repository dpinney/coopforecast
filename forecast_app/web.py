from flask import Flask, render_template, url_for
import pandas as pd

app = Flask(__name__)


@app.route("/")
def login():
    return render_template("login.html", name="login")


@app.route("/load-data")
def load_data():
    df = pd.read_csv("forecast_app/static/test-data/ercot-ncent-load.csv")
    table = df.to_dict("records")
    charts = {
        "2012": [
            0,
            10000,
            5000,
            15000,
            10000,
            20000,
            15000,
            25000,
            20000,
            30000,
            25000,
            40000,
        ],
        "2013": [
            0,
            10000,
            5000,
            15000,
            10000,
            20000,
            15000,
            25000,
            20000,
            30000,
            25000,
            40000,
        ],
        "2014": [
            0,
            10000,
            5000,
            15000,
            10000,
            20000,
            15000,
            25000,
            20000,
            30000,
            25000,
            40000,
        ],
    }
    return render_template(
        "load-data.html", name="load-data", table=table, charts=charts
    )


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
