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


def upload_demo_data():
    """Uploads the demo data to the database."""
    demo_data = Path("forecast_app/static/demo-data")

    # Load historical data
    historical_data = demo_data / "demo-ncent-historical.csv"
    df = pd.read_csv(historical_data, parse_dates=["timestamp"])
    for _, row in df.iterrows():
        new_row = HistoricalData(
            timestamp=row["timestamp"],
            load=row["load"],
            tempc=row["tempc"],
        )
        db.session.add(new_row)
    db.session.commit()
    print("Historical data uploaded.")

    # Load forecast data
    forecast_data = demo_data / "demo-ncent-forecast.csv"
    df = pd.read_csv(forecast_data, parse_dates=["timestamp"])
    for _, row in df.iterrows():
        new_row = ForecastData(
            timestamp=row["timestamp"],
            tempc=row["tempc"],
        )
        db.session.add(new_row)
    db.session.commit()
    print("Forecast data uploaded.")

    mock_model = ForecastModel()
    mock_model.loads = df["load"].tolist()
    mock_model.exited_successfully = True
    mock_model.accuracy = {"test": 96.5, "train": 98.5}
    mock_model.save()
    print("First forecast model uploaded.")

    time.sleep(1)
    mock_model = ForecastModel()
    mock_model.loads = df["load"].tolist()
    mock_model.exited_successfully = False
    mock_model.accuracy = None
    mock_model.save()
    print("Second forecast model uploaded.")
