import os
from flask import Flask, request, render_template, redirect, url_for, flash
import flask_login
from flask_login import (
    UserMixin,
    login_required,
    login_user,
    logout_user,
    current_user,
)

from forecast_app.utils import RenderTemplateView, executor, login_manager
from forecast_app.views import (
    HistoricalLoadDataView,
    ForecastWeatherDataView,
    HistoricalWeatherDataView,
    ForecastView,
    LoginView,
    LogoutView,
)
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

    # Initialize flask-login
    login_manager.init_app(app)

    app.config["UPLOAD_FOLDER"] = "forecast_app/static/uploads"
    app.config["SECRET_KEY"] = "super secret key"

    app.add_url_rule("/login", view_func=LoginView.as_view("login"))
    app.add_url_rule("/logout", view_func=LogoutView.as_view("logout"))
    app.add_url_rule(
        "/historical-load-data",
        view_func=HistoricalLoadDataView.as_view("historical-load-data"),
        methods=["GET", "POST"],
    )

    app.add_url_rule(
        "/forecast-weather-data",
        view_func=ForecastWeatherDataView.as_view("forecast-weather-data"),
    )
    app.add_url_rule(
        "/historical-weather-data",
        view_func=HistoricalWeatherDataView.as_view("historical-weather-data"),
    )
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

    executor.init_app(app)

    return app
