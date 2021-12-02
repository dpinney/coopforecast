import os
import click
from flask.cli import with_appcontext
from pathlib import Path
import pandas as pd

from forecast_app import db
from forecast_app.models import HistoricalData


@click.command("upload-load-data")
@with_appcontext
def upload_load_data():
    test_data = Path("forecast_app/static/test-data") / "ercot-ncent-load.csv"
    df = pd.read_csv(test_data, parse_dates=["timestamp"])
    for i, row in df.iterrows():
        new_row = HistoricalData(timestamp_dt=row["timestamp"], load=row["load"])
        db.session.add(new_row)
    db.session.commit()
