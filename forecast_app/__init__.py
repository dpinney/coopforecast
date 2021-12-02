from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from forecast_app.utils import RenderTemplateView
from forecast_app.views import LoadDataView, WeatherDataView, ForecastView
from forecast_app.db import db_session, init_db_command


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

    app.cli.add_command(init_db_command)

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

    return app
