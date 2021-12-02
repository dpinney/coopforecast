from flask import Flask
from flask import Flask, render_template, url_for
import json
import pandas as pd

from forecast_app.utils import (
    RenderTemplateView,
    transform_timeseries_df_for_highcharts,
)
from forecast_app.views import LoadDataView, WeatherDataView, ForecastView


def create_app():
    app = Flask(__name__)
    app.add_url_rule("/", view_func=RenderTemplateView.view("login"))
    app.add_url_rule("/load-data", view_func=LoadDataView.as_view("load-data"))
    app.add_url_rule("/weather-data", view_func=WeatherDataView.as_view("weather-data"))
    app.add_url_rule("/instructions", view_func=RenderTemplateView.view("instructions"))
    app.add_url_rule("/forecast", view_func=ForecastView.as_view("forecast"))
    app.add_url_rule(
        "/model-settings", view_func=RenderTemplateView.view("model-settings")
    )
    app.add_url_rule(
        "/user-settings", view_func=RenderTemplateView.view("user-settings")
    )

    return app
