from flask import Flask
import atexit

from forecast_app.executor import executor
from forecast_app.utils import (
    login_manager,
    ADMIN_USER,
    db,
)
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
from forecast_app.config import config_map


def create_app(config: str):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_map[config])

    # Ensure that secret_config is set when deploying production
    if app.config["ADMIN_USER"] is None or app.config["ADMIN_PASSWORD"] is None:
        raise ValueError(
            "ADMIN_USER and ADMIN_PASSWORD must be defined in secret_config.py"
        )

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

    # Initialize executor
    executor.init_app(app)
    from forecast_app.executor import close_running_threads

    atexit.register(close_running_threads)

    return app
