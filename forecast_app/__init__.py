import os
from flask import Flask, request, render_template, redirect, url_for, flash
import flask_login

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

    method_views = [
        LoginView,
        LogoutView,
        ForecastView,
        HistoricalLoadDataView,
        ForecastWeatherDataView,
        HistoricalWeatherDataView,
    ]
    for view in method_views:
        app.add_url_rule(
            view.view_url if hasattr(view, "view_url") else f"/{view.view_name}",
            view_func=view.as_view(view.view_name),
        )

    static_views = ["instructions", "model-settings", "user-settings"]
    for view in static_views:
        app.add_url_rule(f"/{view}", view_func=RenderTemplateView.as_view(view))

    app.cli.add_command(init_db_command)
    app.cli.add_command(upload_demo_data_command)

    executor.init_app(app)

    return app
