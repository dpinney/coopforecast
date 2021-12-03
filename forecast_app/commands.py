import os
import click
from flask.cli import with_appcontext
from pathlib import Path
import pandas as pd

from forecast_app import db
from forecast_app.models import ForecastData, HistoricalData
from forecast_app.utils import get_or_create


@click.command("upload-demo-data")
@with_appcontext
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
    click.echo("Historical data uploaded.")

    # Load forecast data
    forecast_data = demo_data / "demo-ncent-forecast.csv"
    df = pd.read_csv(forecast_data, parse_dates=["timestamp"])
    for _, row in df.iterrows():
        new_row = ForecastData(
            timestamp=row["timestamp"],
            load=row["load"],
            tempc=row["tempc"],
        )
        db.session.add(new_row)
    db.session.commit()
    click.echo("Forecast data uploaded.")
