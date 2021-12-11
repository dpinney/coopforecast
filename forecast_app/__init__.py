import os
from flask import Flask, flash, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

from forecast_app.utils import RenderTemplateView
from forecast_app.views import LoadDataView, WeatherDataView, ForecastView
from forecast_app.db import session, init_db_command
from forecast_app.commands import upload_demo_data


def create_app():
    app = Flask(__name__)

    # TODO: Add config file
    app.config["UPLOAD_FOLDER"] = "forecast_app/static/uploads"
    app.config["SECRET_KEY"] = "super secret key"

    app.add_url_rule("/", view_func=RenderTemplateView.view("login"))
    app.add_url_rule(
        "/load-data",
        view_func=LoadDataView.as_view("load-data"),
        methods=["GET", "POST"],
    )

    app.add_url_rule("/weather-data", view_func=WeatherDataView.as_view("weather-data"))
    app.add_url_rule("/instructions", view_func=RenderTemplateView.view("instructions"))
    app.add_url_rule("/forecast", view_func=ForecastView.as_view("forecast"))
    app.add_url_rule(
        "/model-settings", view_func=RenderTemplateView.view("model-settings")
    )
    app.add_url_rule(
        "/user-settings", view_func=RenderTemplateView.view("user-settings")
    )

    app.cli.add_command(init_db_command)
    app.cli.add_command(upload_demo_data)

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        session.remove()

    return app
