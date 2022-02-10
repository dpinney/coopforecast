from flask import Flask
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
    ForecastModelDetailView,
)
from forecast_app.models import HistoricalData
from forecast_app.config import config_map, SECRET_VARS


def create_app(config: str):
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
        LoginView,
        LogoutView,
        ForecastView,
        HistoricalLoadDataView,
        ForecastWeatherDataView,
        HistoricalWeatherDataView,
        ForecastModelListView,
        ForecastModelDetailView,
    ]
    for view in method_views:
        app.add_url_rule(
            view.view_url if hasattr(view, "view_url") else f"/{view.view_name}",
            view_func=view.as_view(view.view_name),
        )

    static_views = ["instructions", "user-settings", "model-settings"]
    for view in static_views:
        app.add_url_rule(f"/{view}", view_func=RenderTemplateView.view(view))

    # TODO: Put this in proper class
    @app.route("/historical-weather-data/sync", methods=["POST"])
    def sync_asos():
        HistoricalData.query.first()

    return app
