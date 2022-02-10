import pandas as pd
from flask import render_template, redirect, url_for, request, current_app
from flask.views import MethodView, View
import flask_login
from sqlalchemy import desc
import time
import datetime
from multiprocessing import Process
from datetime import date, timedelta

from forecast_app.models import ForecastData, HistoricalData, ForecastModel
from forecast_app.utils import db, ADMIN_USER, upload_file
from forecast_app.weather import AsosRequest, NwsForecastRequest


class DataView(MethodView):
    """Abstract class for handling the various views for uploading and
    displaying historical and forecast data"""

    decorators = [flask_login.login_required]
    # TODO: This should be named "model" not "view"
    view = None
    view_key = None
    view_name = None
    title = None
    gist_example = None
    instructions = None
    hide_table = None
    # Variable for whether user can sync data with external API
    sync_request = None

    def get_table(self):
        query = db.session.query(
            self.view.timestamp,
            getattr(self.view, self.view_key),
        )
        query = query.order_by(desc(self.view.timestamp))
        return [
            {"timestamp": timestamp, self.view_key: value} for timestamp, value in query
        ]

    def get_chart(self):
        query = db.session.query(
            self.view.milliseconds, getattr(self.view, self.view_key)
        )
        data = [list(row) for row in query]
        return data if data and any([row[1] for row in query]) else None

    def post(self):
        filepath = upload_file("file")
        # NOTE: if you take advantage of the `columns` parameter, you must
        #  update the cli.py::post_data
        messages = self.view.load_data(filepath)
        return self.get(messages=messages)  # NOTE: A redirect wouldn't work here

    def get(self, messages=None):
        if not messages:
            messages = []

        # NOTE: Just pass self?
        return render_template(
            f"data-view.html",
            **{
                "name": self.view_name,
                "table": self.get_table(),
                "chart": self.get_chart(),
                "messages": messages,
                "title": self.title,
                "data_name": self.view_key,
                "gist_example": self.gist_example,
                "instructions": self.instructions,
                "hide_table": self.hide_table,
                "sync_request": self.sync_request,
            },
        )


class ForecastWeatherDataView(DataView):
    view = ForecastData
    view_key = "tempc"
    view_name = "forecast-weather-data"
    title = "Forecast Weather Data"
    gist_example = "https://gist.github.com/kmcelwee/e56308a8096356fcdc699ca168904aa4"
    instructions = "/instructions#forecast-weather-data"
    hide_table = False
    sync_request = "The National Weather Service"


class HistoricalLoadDataView(DataView):
    view = HistoricalData
    view_key = "load"
    view_name = "historical-load-data"
    title = "Historical Load Data"
    gist_example = "https://gist.github.com/kmcelwee/ce163d8c9d2871ab4c652382431c7801"
    instructions = "/instructions#historical-load-data"
    hide_table = True


class HistoricalWeatherDataView(DataView):
    view = HistoricalData
    view_key = "tempc"
    view_name = "historical-weather-data"
    title = "Historical Weather Data"
    gist_example = "https://gist.github.com/kmcelwee/e56308a8096356fcdc699ca168904aa4"
    instructions = "/instructions#historical-weather-data"
    hide_table = True
    sync_request = "ASOS"


class ForecastView(MethodView):
    view_name = "latest-forecast"
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

    # TODO: Move me to ForecastModelDetailView
    def post(self, mock=False):
        new_model = ForecastModel()
        new_model.save()
        print(f"Starting model {new_model.creation_date}")
        # NOTE: For testing, send 'mock' as a parameter to avoid lengthy training
        # NOTe: "submit_stored" doesn't seem to work as expected
        if request.values.get("mock") == "true":
            process = Process(target=time.sleep, args=(3,))
        else:
            process = Process(
                target=new_model.launch_model, args=(current_app.config["NAME"],)
            )
        process.start()
        new_model.store_process_id(process.pid)
        return redirect(url_for("forecast-model-list"))

    def get(self, messages=None):
        # TODO: Replace this with session data
        #  https://stackoverflow.com/questions/17057191/redirect-while-passing-arguments
        if not messages:
            messages = []

        # Filter by exited_successfully
        # NOTE: Need to do manually because of exited_successfully being a property
        query = (
            db.session.query(ForecastModel)
            .order_by(desc(ForecastModel.creation_date))
            .all()
        )

        for model in query:
            if model.exited_successfully:
                latest_successful_forecast = model
                break
        else:
            latest_successful_forecast = None

        is_prepared, start_date, end_date = ForecastModel.is_prepared()

        return render_template(
            "latest-forecast.html",
            name="latest-forecast",
            chart=self.get_chart(latest_successful_forecast),
            forecast_model=latest_successful_forecast,
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
            return redirect(url_for("latest-forecast"))
        # NOTE: Some kind of attribute error is preventing me from simply using
        #  self.get(error=error). It's not occuring in other pages.
        return redirect(url_for("login", error="Incorrect username and/or password."))

    def get(self):
        if flask_login.current_user.is_authenticated:
            return redirect(url_for("latest-forecast"))
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
    view_name = "forecast-model-list"
    view_url = "/forecast-models"

    def post(self):
        # Cancel all models
        for model in ForecastModel.query.all():
            if model.is_running:
                model.cancel()
        messages = [{"level": "info", "text": "All running models were terminated."}]
        return self.get(messages=messages)

    def get(self, messages=None):
        # messages = request.args.get("messages", [])
        messages = [] if messages is None else messages
        models = ForecastModel.query.order_by(desc(ForecastModel.creation_date)).all()
        (
            model_is_prepared,
            model_start_date,
            model_end_date,
        ) = ForecastModel.is_prepared()
        hd_is_prepared, hd_start_date, hd_end_date = HistoricalData.is_prepared()
        fd_is_prepared, fd_start_date, fd_end_date = ForecastData.is_prepared()

        return render_template(
            "forecast-model-list.html",
            models=models,
            model_is_prepared=model_is_prepared,
            model_start_date=model_start_date,
            model_end_date=model_end_date,
            hd_is_prepared=hd_is_prepared,
            hd_start_date=hd_start_date,
            hd_end_date=hd_end_date,
            fd_is_prepared=fd_is_prepared,
            fd_start_date=fd_start_date,
            fd_end_date=fd_end_date,
            messages=messages,
        )


class ForecastModelDetailView(MethodView):
    view_name = "forecast-model-detail"
    view_url = "/forecast-models/<slug>"
    decorators = [flask_login.login_required]
    # TODO:
    # - make model downloadable

    def get_chart(self, forecast):
        if forecast and forecast.loads:
            return [
                [timestamp, load]
                for load, timestamp in zip(forecast.loads, forecast.milliseconds)
            ]
        else:
            return None

    def get(self, slug, messages=None):
        if not messages:
            messages = []

        forecast_model = ForecastModel.query.filter_by(slug=slug).first()

        return render_template(
            "forecast-model-detail.html",
            name="forecast",
            chart=self.get_chart(forecast_model),
            forecast_model=forecast_model,
            messages=messages,
        )


class DataSync(MethodView):
    view_name = None
    view_url = None
    endpoint_class = None

    def post(self):
        return redirect(url_for(self.view_name.split("-sync")[0]))

    def get(self):
        return redirect(url_for(self.view_name.split("-sync")[0]))


class HistoricalWeatherDataSync(DataSync):
    view_name = "historical-weather-data-sync"
    view_url = "/historical-weather-data/sync"
    endpoint_class = AsosRequest

    def post(self):

        temp_query = HistoricalData.query.filter(HistoricalData.tempc.isnot(None))
        if temp_query.count() > 0:
            # Get the latest sync timestamp as the start date
            start_date = (
                temp_query.order_by(HistoricalData.timestamp.desc())
                .first()
                .timestamp.date()
            )
        else:
            # If the database is empty, use the start date provided by the config
            start_date = current_app.config["EARLIEST_SYNC_DATE"]

        asos_request = AsosRequest(
            start_date=start_date,
            end_date=date.today() + timedelta(days=1),
            tz=current_app.config["TIMEZONE"],
            station=current_app.config["ASOS_STATION"],
        )
        request = asos_request.send_request()
        df = asos_request.create_df()
        HistoricalData.load_df(df)
        return super().post()


class ForecastWeatherDataSync(DataSync):
    view_name = "forecast-weather-data-sync"
    view_url = "/forecast-weather-data/sync"
