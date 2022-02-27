"""Base module for the application, imports of all utilities, models, and views go through here."""

import logging

from flask import Flask, render_template, redirect
from forecast_app.utils import (
    login_manager,
    ADMIN_USER,
    db,
)
from forecast_app import views
from forecast_app.config import config_map, SECRET_VARS


def create_app(config: str):
    """A factory function that creates the flask app with the given configuration."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_map[config])

    # Ensure that secret_config is set when deploying production
    if any([app.config[var] is None for var in SECRET_VARS]):
        undefined = [var for var in SECRET_VARS if app.config[var] is None]
        raise ValueError(
            f"These secret vars must be defined in secret_config.py: {undefined}"
        )

    # Initialize database
    db.init_app(app)

    # Initialize flask-login
    login_manager.init_app(app)
    ADMIN_USER.id = app.config["ADMIN_USER"]

    method_views = [
        views.LoginView,
        views.LogoutView,
        views.LatestForecastView,
        views.HistoricalLoadDataView,
        views.ForecastWeatherDataView,
        views.HistoricalWeatherDataView,
        views.ForecastModelListView,
        views.ForecastModelDetailView,
        views.HistoricalWeatherDataSync,
        views.ForecastWeatherDataSync,
        views.DownloadModelFiles,
    ]
    for view in method_views:
        app.add_url_rule(
            view.view_url if hasattr(view, "view_url") else f"/{view.view_name}",
            view_func=view.as_view(view.view_name),
            strict_slashes=False,
        )

    static_views = ["instructions", "user-settings", "model-settings"]
    for view in static_views:
        app.add_url_rule(
            f"/{view}",
            view_func=views.RenderTemplateView.view(view),
            strict_slashes=False,
        )

    # Error handlers ==================
    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html")

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template("500.html")

    @app.route("/500-trigger")
    def trigger_500():
        raise Exception("500 error triggered")

    @app.errorhandler(401)
    def unauthorized(e):
        """If a user tries to access a page that requires authentication, redirect them to the login page."""
        return redirect("/", code=302)

    # Link Gunicorn logging
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

    return app
