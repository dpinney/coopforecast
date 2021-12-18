import pandas as pd
from flask import render_template, redirect, url_for, request, current_app
from flask.views import MethodView, View
import flask_login

from forecast_app.models import ForecastData, HistoricalData, ForecastModel
from forecast_app.utils import db
from forecast_app.utils import ADMIN_USER, upload_file, executor


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
        return redirect(url_for("login", error="Incorrect password."))

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
