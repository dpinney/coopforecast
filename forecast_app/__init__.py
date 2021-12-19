import os
from flask import Flask, request, render_template, redirect, url_for, flash
import flask_login

from forecast_app.utils import executor, login_manager, ADMIN_USER, db
from forecast_app.views import (
    HistoricalLoadDataView,
    ForecastWeatherDataView,
    HistoricalWeatherDataView,
    ForecastView,
    LoginView,
    LogoutView,
    RenderTemplateView,
    ForecastModelListView,
)


def create_app(config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config)

    # Initialize database
    db.init_app(app)

    # Initialize flask-login
    login_manager.init_app(app)
    ADMIN_USER.id = app.config["ADMIN_USER"]

    method_views = [
        LoginView,
        LogoutView,
        ForecastView,
        HistoricalLoadDataView,
        ForecastWeatherDataView,
        HistoricalWeatherDataView,
        ForecastModelListView,
    ]
    for view in method_views:
        app.add_url_rule(
            view.view_url if hasattr(view, "view_url") else f"/{view.view_name}",
            view_func=view.as_view(view.view_name),
        )

    static_views = ["instructions", "model-settings", "user-settings"]
    for view in static_views:
        app.add_url_rule(f"/{view}", view_func=RenderTemplateView.view(view))

    executor.init_app(app)

    return app
