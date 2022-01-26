import os
from pathlib import Path
import pandas as pd
import time
from flask import current_app

from forecast_app.utils import db
from forecast_app.models import ForecastData, ForecastModel, HistoricalData


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
    historical_data = demo_data / "demo-ncent-historical.csv"
    HistoricalData.load_data(historical_data)
    print("Historical data uploaded.")

    # Load forecast data
    forecast_data = demo_data / "demo-ncent-forecast.csv"
    ForecastData.load_data(forecast_data, columns=[current_app.config["TEMP_COL"]])
    print("Forecast data uploaded.")

    if models:
        mock_load = pd.read_csv(forecast_data)[current_app.config["LOAD_COL"]].tolist()
        mock_model = ForecastModel()
        mock_model.loads = mock_load
        mock_model.accuracy = {"test": 96.5, "train": 98.5}
        mock_model.store_process_id("COMPLETED")
        mock_model.save()
        print("First forecast model uploaded.")

        mock_model = ForecastModel()
        mock_model.loads = mock_load
        mock_model.accuracy = None
        mock_model.save()
        print("Second forecast model uploaded.")

        mock_model = ForecastModel()
        mock_model.loads = mock_load
        mock_model.accuracy = None
        mock_model.save()
        print("Third forecast model uploaded.")
