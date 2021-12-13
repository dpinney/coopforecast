import pandas as pd
from flask import render_template, redirect, url_for
from flask.views import MethodView, View

from forecast_app.models import ForecastData, HistoricalData
from forecast_app.db import db
from forecast_app.utils import upload_file

import sys


class LoadDataView(MethodView):
    def get_table(self):
        query = db.session.query(HistoricalData.timestamp, HistoricalData.load)
        return [{"load": load, "timestamp": timestamp} for timestamp, load in query]

    def get_chart(self):
        query = db.session.query(HistoricalData.milliseconds, HistoricalData.load)
        return [list(row) for row in query]

    def post(self):
        filepath = upload_file("file")
        HistoricalData.load_data(filepath)
        # TODO: Signal to user that data was uploaded
        return redirect(url_for("load-data"))

    def get(self):
        return render_template(
            "load-data.html",
            **{
                "name": "load-data",
                "table": self.get_table(),
                "chart": self.get_chart(),
            }
        )


class WeatherDataView(View):
    def get_forecast_table(self):
        query = db.session.query(ForecastData.milliseconds, ForecastData.tempc)
        return [{"tempc": temp, "timestamp": timestamp} for timestamp, temp in query]

    def get_historical_table(self):
        query = db.session.query(HistoricalData.milliseconds, HistoricalData.tempc)
        return [{"tempc": temp, "timestamp": timestamp} for timestamp, temp in query]

    def get_forecast_chart(self):
        query = db.session.query(ForecastData.milliseconds, ForecastData.tempc)
        return [list(row) for row in query]

    def get_historical_chart(self):
        query = db.session.query(HistoricalData.milliseconds, HistoricalData.tempc)
        return [list(row) for row in query]

    def dispatch_request(self):
        return render_template(
            "weather-data.html",
            **{
                "name": "weather-data",
                "tables": [
                    self.get_forecast_table(),
                    self.get_historical_table(),
                ],
                "forecast_chart": self.get_forecast_chart(),
                "historical_chart": self.get_historical_chart(),
            }
        )


class ForecastView(View):
    def get_forecast_chart(self):
        query = db.session.query(ForecastData.milliseconds, ForecastData.load)
        return [list(row) for row in query]

    def dispatch_request(self):

        return render_template(
            "forecast.html",
            name="forecast",
            chart=self.get_forecast_chart(),
        )
