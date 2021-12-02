from flask import Flask
from flask import Flask, render_template, url_for
import json
import pandas as pd

from forecast_app.utils import (
    RenderTemplateView,
    transform_timeseries_df_for_highcharts,
)
from forecast_app.views import LoadDataView, WeatherDataView


def create_app():
    app = Flask(__name__)
    app.add_url_rule("/", view_func=RenderTemplateView.view("login"))
    app.add_url_rule("/load-data", view_func=LoadDataView.as_view("load-data"))
    app.add_url_rule("/weather-data", view_func=WeatherDataView.as_view("weather-data"))
    app.add_url_rule("/instructions", view_func=RenderTemplateView.view("instructions"))

    @app.route("/forecast")
    def forecast():
        df = pd.read_csv(
            "forecast_app/static/test-data/mock-forecast-load.csv",
            parse_dates=["timestamp"],
        )

        return render_template(
            "forecast.html",
            name="forecast",
            chart=transform_timeseries_df_for_highcharts(df, value="load"),
        )

    @app.route("/model-settings")
    def model_settings():
        return render_template("model-settings.html", name="model-settings")

    @app.route("/user-settings")
    def user_settings():
        return render_template("user-settings.html", name="user-settings")

    return app
