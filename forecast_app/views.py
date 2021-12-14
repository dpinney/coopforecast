import pandas as pd
from flask import render_template, redirect, url_for
from flask.views import MethodView, View

from forecast_app.models import ForecastData, HistoricalData
from forecast_app.db import db
from forecast_app.utils import upload_file


class HistoricalLoadDataView(MethodView):
    def get_table(self):
        query = db.session.query(HistoricalData.timestamp, HistoricalData.load)
        return [{"load": load, "timestamp": timestamp} for timestamp, load in query]

    def get_chart(self):
        query = db.session.query(HistoricalData.milliseconds, HistoricalData.load)
        return [list(row) for row in query]

    def post(self):
        filepath = upload_file("file")
        messages = HistoricalData.load_data(filepath)
        return self.get(messages=messages)  # NOTE: A redirect wouldn't work here

    def get(self, messages=[]):
        return render_template(
            "historical-load-data.html",
            **{
                "name": "historical-load-data",
                "table": self.get_table(),
                "chart": self.get_chart(),
                "messages": messages,
            },
        )


class HistoricalWeatherDataView(View):
    def get_table(self):
        query = db.session.query(HistoricalData.milliseconds, HistoricalData.tempc)
        return [{"tempc": temp, "timestamp": timestamp} for timestamp, temp in query]

    def get_chart(self):
        query = db.session.query(HistoricalData.milliseconds, HistoricalData.tempc)
        return [list(row) for row in query]

    def dispatch_request(self):
        return render_template(
            "historical-weather-data.html",
            **{
                "name": "historical-weather-data",
                "table": self.get_table(),
                "chart": self.get_chart(),
            },
        )


class ForecastWeatherDataView(View):
    def get_table(self):
        query = db.session.query(ForecastData.milliseconds, ForecastData.tempc)
        return [{"tempc": temp, "timestamp": timestamp} for timestamp, temp in query]

    def get_chart(self):
        query = db.session.query(ForecastData.milliseconds, ForecastData.tempc)
        return [list(row) for row in query]

    def dispatch_request(self):
        return render_template(
            "forecast-weather-data.html",
            **{
                "name": "forecast-weather-data",
                "table": self.get_table(),
                "chart": self.get_chart(),
            },
        )


class ForecastView(View):
    def get_chart(self):
        query = db.session.query(ForecastData.milliseconds, ForecastData.load)
        return [list(row) for row in query]

    def dispatch_request(self):

        return render_template(
            "forecast.html",
            name="forecast",
            chart=self.get_chart(),
        )
