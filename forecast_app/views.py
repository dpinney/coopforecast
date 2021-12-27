import pandas as pd
from flask import render_template, redirect, url_for, request, current_app
from flask.views import MethodView, View
import flask_login
from sqlalchemy import desc
import time

from forecast_app.models import ForecastData, HistoricalData, ForecastModel
from forecast_app.utils import db
from forecast_app.utils import ADMIN_USER, upload_file
from forecast_app.executor import executor


class DataView(MethodView):
    decorators = [flask_login.login_required]
    view = None
    view_key = None
    view_name = None

    def get_table(self):
        query = db.session.query(
            self.view.timestamp,
            getattr(self.view, self.view_key),
        )
        return [
            {"timestamp": timestamp, self.view_key: temp} for timestamp, temp in query
        ]

    def get_chart(self):
        query = db.session.query(self.view.milliseconds, self.view.tempc)
        return [list(row) for row in query]

    def post(self):
        filepath = upload_file("file")
        messages = self.view.load_data(filepath)
        return self.get(messages=messages)  # NOTE: A redirect wouldn't work here

    def get(self, messages=None):
        if not messages:
            messages = []

        return render_template(
            f"{self.view_name}.html",
            **{
                "name": self.view_name,
                "table": self.get_table(),
                "chart": self.get_chart(),
                "messages": messages,
            },
        )


class ForecastWeatherDataView(DataView):
    view = ForecastData
    view_key = "tempc"
    view_name = "forecast-weather-data"


class HistoricalLoadDataView(DataView):
    view = HistoricalData
    view_key = "load"
    view_name = "historical-load-data"


class HistoricalWeatherDataView(DataView):
    view = HistoricalData
    view_key = "tempc"
    view_name = "historical-weather-data"


class ForecastView(MethodView):
    view_name = "forecast"
    decorators = [flask_login.login_required]
    # TODO:
    # - make model downloadable
    # - display messages about why data is not prepared

    def get_chart(self, forecast):
        if forecast:
            return [
                [timestamp, load]
                for load, timestamp in zip(forecast.loads, forecast.milliseconds)
            ]
        else:
            return None

    def post(self, mock=False):
        new_model = ForecastModel()
        new_model.is_running = True
        new_model.save()
        print(f"Starting model {new_model.creation_date}")
        # NOTE: For testing, send 'mock' as a parameter to avoid lengthy training
        if request.values.get("mock") == "true":
            executor.submit_stored(new_model.creation_date, time.sleep, 1000)
        else:
            executor.submit_stored(new_model.creation_date, new_model.launch_model)
        return self.get(messages=[{"level": "info", "text": "Forecast started"}])

    def get_running_models(self):
        return db.session.query(ForecastModel).filter_by(is_running=True).all()

    def get(self, messages=None):
        if not messages:
            messages = []

        # Filter by exited_successfully
        latest_successful_forecast = (
            db.session.query(ForecastModel)
            .filter_by(exited_successfully=True)
            .order_by(desc(ForecastModel.creation_date))
            .first()
        )

        is_prepared, start_date, end_date = ForecastModel.is_prepared()

        return render_template(
            "forecast.html",
            name="forecast",
            chart=self.get_chart(latest_successful_forecast),
            running_models=self.get_running_models(),
            forecast=latest_successful_forecast,
            # Is the data prepared for a new forecast?
            is_prepared=is_prepared,
            start_date=start_date,
            end_date=end_date,
            messages=messages,
        )


class LoginView(MethodView):
    view_name = "login"
    view_url = "/"

    def post(self):
        if request.form.get("password") == current_app.config["ADMIN_PASSWORD"]:
            remember = request.form.get("remember-me") == "on"
            flask_login.login_user(ADMIN_USER, remember=remember)
            return redirect("/forecast")
        # NOTE: Some kind of attribute error is preventing me from simply using
        #  self.get(error=error). It's not occuring in other pages.
        return redirect(url_for("login", error="Incorrect username and/or password."))

    def get(self):
        if flask_login.current_user.is_authenticated:
            return redirect(url_for("forecast"))
        return render_template("login.html")


class LogoutView(MethodView):
    view_name = "logout"

    def get(self):
        flask_login.logout_user()
        return redirect("/")


class RenderTemplateView(View):
    decorators = [flask_login.login_required]

    def __init__(self, template_name):
        self.template_name = template_name

    def dispatch_request(self):
        return render_template(self.template_name)

    @classmethod
    def view(cls, name, template=None):
        if not template:
            template = name + ".html"
        return cls.as_view(name, template_name=template)


class ForecastModelListView(MethodView):
    decorators = [flask_login.login_required]
    view_name = "forecast-models"

    def get(self):
        models = ForecastModel.query.order_by(desc(ForecastModel.creation_date)).all()
        return render_template("forecast-models.html", models=models)
