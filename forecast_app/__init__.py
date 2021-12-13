import os
from flask import Flask, flash, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

from forecast_app.utils import RenderTemplateView
from forecast_app.views import LoadDataView, WeatherDataView, ForecastView
from forecast_app.db import db, init_db_command
from forecast_app.commands import upload_demo_data_command


def create_app(test_config={}):
    app = Flask(__name__, instance_relative_config=True)

    # TODO: Add config file
    # app.config.from_pyfile("config.py", silent=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////tmp/test.db"  # CHANGE ME
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config.update(test_config)

    # Initialize database
    app.app_context().push()
    db.init_app(app)

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
    app.cli.add_command(upload_demo_data_command)

    return app
