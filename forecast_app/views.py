import pandas as pd
from flask import render_template, redirect, url_for
from flask.views import MethodView, View
import tensorflow as tf

from forecast_app.models import ForecastData, HistoricalData
from forecast_app.db import db
from forecast_app.utils import upload_file


class DataView(MethodView):
    data_class = None
    data_class_key = None
    data_class_name = None

    def get_table(self):
        query = db.session.query(
            self.data_class.milliseconds,
            getattr(self.data_class, self.data_class_key),
        )
        return [
            {self.data_class_key: temp, "timestamp": timestamp}
            for timestamp, temp in query
        ]

    def get_chart(self):
        query = db.session.query(self.data_class.milliseconds, self.data_class.tempc)
        return [list(row) for row in query]

    def post(self):
        filepath = upload_file("file")
        messages = self.data_class.load_data(filepath)
        return self.get(messages=messages)  # NOTE: A redirect wouldn't work here

    def get(self, messages=None):
        return render_template(
            f"{self.data_class_name}.html",
            **{
                "name": self.data_class_name,
                "table": self.get_table(),
                "chart": self.get_chart(),
                "messages": messages,
            },
        )


class ForecastWeatherDataView(DataView):
    data_class = ForecastData
    data_class_key = "tempc"
    data_class_name = "forecast-weather-data"


class HistoricalLoadDataView(DataView):
    data_class = HistoricalData
    data_class_key = "load"
    data_class_name = "historical-load-data"


class HistoricalWeatherDataView(DataView):
    data_class = HistoricalData
    data_class_key = "tempc"
    data_class_name = "historical-weather-data"


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
