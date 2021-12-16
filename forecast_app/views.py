import pandas as pd
from flask import render_template, redirect, url_for
from flask.views import MethodView, View
import tensorflow as tf

from forecast_app.models import ForecastData, HistoricalData, ForecastModel
from forecast_app.db import db
from forecast_app.utils import upload_file, executor


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
        if not messages:
            messages = []

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


class ForecastView(MethodView):
    # TODO:
    # - make model downloadable
    # - display messages about why data is not prepared

    def check_data_preparation(self, messages):
        # If data is prepared and no model exists
        # messages.append({"level": "info", "text": "Data is not prepared"})
        pass

    def get_chart(self, forecast):
        if forecast:
            return [
                [timestamp, load]
                for load, timestamp in zip(forecast.loads, forecast.milliseconds)
            ]
        else:
            return None

    def post(self):
        new_model = ForecastModel()
        new_model.save()
        print(f"Starting model {new_model.creation_date}")
        executor.submit(new_model.launch_model)
        print(f"Ending model {new_model.creation_date}")
        return self.get(messages=[{"level": "info", "text": "Forecast started"}])

    def get_running_models(self):
        return [model for model in db.session.query(ForecastModel) if model.is_running]

    def get(self, messages=None):
        if not messages:
            messages = []
        self.check_data_preparation(messages)

        # Filter by exited_successfully
        latest_successful_forecast = (
            db.session.query(ForecastModel)
            .filter_by(exited_successfully=True)
            .order_by(ForecastModel.creation_date)
            .first()
        )

        return render_template(
            "forecast.html",
            name="forecast",
            chart=self.get_chart(latest_successful_forecast),
            is_running=self.get_running_models(),
            forecast=latest_successful_forecast,
            messages=messages,
        )
