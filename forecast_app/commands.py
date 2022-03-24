"""Model-specific utilities that would otherwise cause circular imports if placed elsewhere."""

from pathlib import Path

import pandas as pd

from forecast_app.models import (
    ForecastModel,
    ForecastWeatherData,
    HistoricalLoadData,
    HistoricalWeatherData,
)
from forecast_app.utils import db


def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    import forecast_app.models

    db.drop_all()
    db.create_all()
    print("Initialized the database.")


def upload_demo_data(models=True):
    """Uploads the demo data to the database."""
    demo_data = Path("forecast_app/static/demo-data")
    # Load historical data
    historical_load_data = demo_data / "demo-ncent-historical-load.csv"
    HistoricalLoadData.load_data(historical_load_data)
    historical_weather_data = demo_data / "demo-ncent-historical-temp.csv"
    HistoricalWeatherData.load_data(historical_weather_data)
    print("Historical data uploaded.")

    # Load forecast data
    forecast_weather_data = demo_data / "demo-ncent-forecast-temp.csv"
    ForecastWeatherData.load_data(forecast_weather_data)
    print("Forecast data uploaded.")

    if models:
        forecast_load_data = demo_data / "demo-ncent-forecast-load.csv"
        mock_load = pd.read_csv(forecast_load_data)["KW"].tolist()
        mock_model = ForecastModel()
        mock_model.loads = mock_load
        mock_model.accuracy = {"test": 4.3, "train": 4.4}
        mock_model.store_process_id(mock_model.COMPLETED_SUCCESSFULLY)

        # Copy the cached dataframe to this mock model's
        df = pd.read_csv(demo_data / "cached-dataframe.csv")
        mock_model.store_df(df)
        mock_model.save()
        print("First forecast model uploaded.")

        mock_model = ForecastModel()
        mock_model.store_df(df)
        mock_model.loads = mock_load
        mock_model.accuracy = None
        mock_model.save()
        print("Second forecast model uploaded.")

        mock_model = ForecastModel()
        mock_model.store_df(df)
        mock_model.loads = mock_load
        mock_model.accuracy = None
        mock_model.save()
        print("Third forecast model uploaded.")
