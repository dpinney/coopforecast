import pandas as pd
from flask import render_template, redirect, url_for, request, current_app
from flask.views import MethodView, View
import flask_login
from sqlalchemy import desc, null
import time
import datetime
from multiprocessing import Process
from datetime import date, timedelta

from forecast_app.models import (
    ForecastWeatherData,
    HistoricalLoadData,
    HistoricalWeatherData,
    ForecastModel,
)
from forecast_app.utils import db, ADMIN_USER, upload_file
from forecast_app.weather import AsosRequest, NwsForecastRequest


class DataView(MethodView):
    """Abstract class for handling the various views for uploading and
    displaying historical and forecast data"""

    decorators = [flask_login.login_required]
    model = None
    view_name = None
    title = None
    gist_example = None
    instructions = None
    hide_table = None
    # Variable for whether user can sync data with external API
    sync_request = None

    def get_missing_values_summary(self):
        df = self.model.to_df()
        col = self.model.column_name

        df = df.set_index("dates")
        cumulative_df = (
            df[col]
            .isnull()
            .astype(int)
            .groupby(df[col].notnull().astype(int).cumsum())
            .cumsum()
        )
        max_span = cumulative_df.max()
        end_datetime = cumulative_df.idxmax()
        # NOTE: timedelta can't take numpy.int64
        start_datetime = end_datetime - datetime.timedelta(hours=int(max_span - 1))
        return {
            "count": df[col].isna().sum(),
            "max_span": max_span,
            "start_datetime": start_datetime,
            "end_datetime": end_datetime,
        }

    def get_summary(self):
        if self.model.query.count() == 0:
            return None

        return {
            "count": self.model.query.count(),
            "start_datetime": self.model.query.order_by(self.model.timestamp)
            .first()
            .timestamp,
            "end_datetime": self.model.query.order_by(self.model.timestamp.desc())
            .first()
            .timestamp,
            "missing_values": self.get_missing_values_summary(),
        }

    def get_table(self):
        query = db.session.query(
            self.model.timestamp,
            self.model.value,
        )
        query = query.order_by(desc(self.model.timestamp))
        return [{"timestamp": timestamp, "value": value} for timestamp, value in query]

    def get_chart(self):
        query = db.session.query(self.model.milliseconds, self.model.value)
        data = [list(row) for row in query]
        return [{"data": data, "name": self.model.column_name}]

    def post(self):
        filepath = upload_file("file")
        messages = self.model.load_data(filepath)
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
                "gist_example": self.gist_example,
                "instructions": self.instructions,
                "hide_table": self.hide_table,
                "sync_request": self.sync_request,
                "summary": self.get_summary(),
            },
        )


class ForecastWeatherDataView(DataView):
    model = ForecastWeatherData
    view_name = "forecast-weather-data"
    title = "Forecast Weather Data"
    gist_example = "https://gist.github.com/kmcelwee/e56308a8096356fcdc699ca168904aa4"
    instructions = "/instructions#forecast-weather-data"
    hide_table = False
    sync_request = "The National Weather Service"


class HistoricalLoadDataView(DataView):
    model = HistoricalLoadData
    view_name = "historical-load-data"
    title = "Historical Load Data"
    gist_example = "https://gist.github.com/kmcelwee/ce163d8c9d2871ab4c652382431c7801"
    instructions = "/instructions#historical-load-data"
    hide_table = True


class HistoricalWeatherDataView(DataView):
    model = HistoricalWeatherData
    view_name = "historical-weather-data"
    title = "Historical Weather Data"
    gist_example = "https://gist.github.com/kmcelwee/e56308a8096356fcdc699ca168904aa4"
    instructions = "/instructions#historical-weather-data"
    hide_table = True
    sync_request = "ASOS"


class LatestForecastView(MethodView):
    """Masked redirect to the latest successful forecast model"""

    view_name = "latest-forecast"
    decorators = [flask_login.login_required]

    def get_latest_successful_model(self):
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

        return latest_successful_forecast

    def get(self):
        model = self.get_latest_successful_model()
        if model:
            return ForecastModelDetailView().get(slug=model.slug, model=model)
        else:
            return render_template("latest-forecast.html")


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

    # TODO: Create a boolean to split post requests or shift to cancelling specific models
    # def post(self):
    #     # Cancel all models
    #     for model in ForecastModel.query.all():
    #         if model.is_running:
    #             model.cancel()
    #     messages = [{"level": "info", "text": "All running models were terminated."}]
    #     return self.get(messages=messages)

    # TODO: mock=False is a hack
    def post(self, mock=False):
        new_model = ForecastModel()
        new_model.save()
        print(f"Starting model {new_model.creation_date}")
        # NOTE: For testing, send 'mock' as a parameter to avoid lengthy training
        # NOTE: "submit_stored" doesn't seem to work as expected
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
        # messages = request.args.get("messages", [])
        messages = [] if messages is None else messages
        models = ForecastModel.query.order_by(desc(ForecastModel.creation_date)).all()
        model_is_prepared = ForecastModel.is_prepared()
        data_is_prepared = {
            "Historical load data": HistoricalLoadData.is_prepared(),
            "Historical weather data": HistoricalWeatherData.is_prepared(),
            "Forecast weather data": ForecastWeatherData.is_prepared(),
        }

        return render_template(
            "forecast-model-list.html",
            models=models,
            model_is_prepared=model_is_prepared,
            data_is_prepared=data_is_prepared,
            messages=messages,
        )


class ForecastModelDetailView(MethodView):
    view_name = "forecast-model-detail"
    view_url = "/forecast-models/<slug>"
    decorators = [flask_login.login_required]
    # TODO:
    # - make model downloadable

    def get_chart(self, forecast):
        if not forecast:
            return None

        # Get training data
        df = forecast.get_df()

        df["timestamp"] = df.dates.apply(lambda x: x.timestamp() * 1000)

        # Get end of load data
        lvi = df["load"].last_valid_index()
        CONTEXT = 72

        context_data = [
            [row.timestamp, row.load]
            for row in df.iloc[lvi - CONTEXT : lvi].itertuples()
        ]
        forecast_data = [
            [ts, load] for load, ts in zip(forecast.loads, forecast.milliseconds)
        ]
        return [
            {
                "data": context_data,
                "name": "Load",
            },
            {
                "data": forecast_data,
                "name": "Forecast",
                "color": "blue",
            },
        ]

    def get(self, slug, messages=None, model=None):
        if not messages:
            messages = []

        if model:
            forecast_model = model
        else:
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
    parent_view = None

    def post(self):
        request = self.build_request()
        request.send_request()
        df = request.create_df()
        self.parent_view.model.load_df(df)
        return redirect(url_for(self.parent_view.view_name))

    def get(self):
        return redirect(url_for(self.parent_view.view_name))


class HistoricalWeatherDataSync(DataSync):
    view_name = "historical-weather-data-sync"
    view_url = "/historical-weather-data/sync"
    endpoint_class = AsosRequest
    parent_view = HistoricalWeatherDataView

    def build_request(self):
        if HistoricalWeatherData.query.count() > 0:
            # Get the latest sync timestamp as the start date
            start_date = (
                HistoricalWeatherData.query.order_by(
                    HistoricalWeatherData.timestamp.desc()
                )
                .first()
                .timestamp.date()
            )
        else:
            # If the database is empty, use the start date provided by the config
            start_date = current_app.config["EARLIEST_SYNC_DATE"]

        return AsosRequest(
            start_date=start_date,
            end_date=date.today() + timedelta(days=1),
            tz=current_app.config["TIMEZONE"],
            station=current_app.config["ASOS_STATION"],
        )


class ForecastWeatherDataSync(DataSync):
    view_name = "forecast-weather-data-sync"
    view_url = "/forecast-weather-data/sync"
    endpoint_class = NwsForecastRequest
    parent_view = ForecastWeatherDataView

    def build_request(self):
        return NwsForecastRequest(nws_code=current_app.config["NWS_CODE"])
