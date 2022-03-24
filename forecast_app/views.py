"""All the views for the forecast app. Each view corresponds to a route."""

import datetime
import os
import time
from datetime import date, timedelta
from multiprocessing import Process

import flask_login
from flask import (
    current_app,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask.views import MethodView, View
from sqlalchemy import desc

from forecast_app import burtcoppd
from forecast_app.models import (
    ForecastModel,
    ForecastWeatherData,
    HistoricalLoadData,
    HistoricalWeatherData,
)
from forecast_app.utils import ADMIN_USER, db, safe_flash, upload_file
from forecast_app.weather import AsosRequest, NwsForecastRequest

# TODO: Set default ordering to milliseconds / timestamps to prevent chart mixups


class DataView(MethodView):
    """Abstract class for handling the various views for uploading and
    displaying historical and forecast data"""

    decorators = [flask_login.login_required]
    model = None
    view_name = None
    title = None
    gist_example = None
    # Variable for whether user can sync data with external API
    sync_request = None

    def get_missing_values_summary(self):
        """Collect basic information about missing values in the given model"""
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
        """Return dictionary for the data views "Data Summary" section."""
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
        """Put data into a format that can be rendered by jinja as a table"""
        query = db.session.query(
            self.model.timestamp,
            self.model.value,
        )
        query = query.order_by(desc(self.model.timestamp))
        return [{"timestamp": timestamp, "value": value} for timestamp, value in query]

    def get_chart(self):
        """Put data into a format that can be rendered by highstock as a chart"""
        query = db.session.query(self.model.milliseconds, self.model.value).order_by(
            self.model.milliseconds
        )
        data = [list(row) for row in query]
        return [{"data": data, "name": self.model.column_name}]

    def post(self):
        """Given a POST request to the data view's endpoint, upload the file and load it into the database"""
        filepath = upload_file("file")
        self.model.load_data(filepath)
        return redirect(url_for(self.view_name))

    def get(self):
        """Render the data view"""
        # NOTE: Just pass self?
        return render_template(
            "data-view.html",
            **{
                "name": self.view_name,
                "table": self.get_table(),
                "chart": self.get_chart(),
                "title": self.title,
                "gist_example": self.gist_example,
                "sync_request": self.sync_request,
                "summary": self.get_summary(),
            },
        )


class ForecastWeatherDataView(DataView):
    """View for the forecast weather data"""

    model = ForecastWeatherData
    view_name = "forecast-weather-data"
    title = "Forecast Weather Data"
    gist_example = "https://gist.github.com/kmcelwee/e56308a8096356fcdc699ca168904aa4"
    sync_request = "The National Weather Service"


class HistoricalLoadDataView(DataView):
    """View for the historical load data"""

    model = HistoricalLoadData
    view_name = "historical-load-data"
    title = "Historical Load Data"
    gist_example = "https://gist.github.com/kmcelwee/ce163d8c9d2871ab4c652382431c7801"


class HistoricalWeatherDataView(DataView):
    """View for the historical weather data"""

    model = HistoricalWeatherData
    view_name = "historical-weather-data"
    title = "Historical Weather Data"
    gist_example = "https://gist.github.com/kmcelwee/e56308a8096356fcdc699ca168904aa4"
    sync_request = "ASOS"


class LatestForecastView(MethodView):
    """Masked redirect to the latest successful forecast model"""

    view_name = "latest-forecast"
    decorators = [flask_login.login_required]

    def get_latest_successful_model(self):
        """Return the latest successful forecast model to show to user in this view"""
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
        """Redirect to the latest successful forecast model if one exists, otherwise show a page with message."""
        model = self.get_latest_successful_model()
        if model:
            return ForecastModelDetailView().get(slug=model.slug)
        return render_template("latest-forecast.html")


class LoginView(MethodView):
    """View for the login page."""

    view_name = "login"
    view_url = "/"

    def post(self):
        """Given a POST request to the login page, authenticate the user and redirect"""
        if (
            request.form.get("password") == current_app.config["ADMIN_PASSWORD"]
            and request.form.get("username") == current_app.config["ADMIN_USER"]
        ):
            remember = request.form.get("remember-me") == "on"
            flask_login.login_user(ADMIN_USER, remember=remember)
            return redirect(url_for("latest-forecast"))
        # NOTE: Some kind of attribute error is preventing me from simply using
        #  self.get(error=error). It's not occuring in other pages.
        safe_flash("Incorrect username and/or password.", "danger")
        return redirect(url_for("login"))

    def get(self):
        """Render the login page"""
        if flask_login.current_user.is_authenticated:
            return redirect(url_for("latest-forecast"))
        return render_template("login.html")


class LogoutView(MethodView):
    """View for the logout page"""

    view_name = "logout"

    def get(self):
        """Logout the user and redirect to the login page"""
        flask_login.logout_user()
        return redirect("/")


class RenderTemplateView(View):
    """Simple view to render any static page, like `instructions.html`."""

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
    """View for the list of all forecast models and generating new ones."""

    decorators = [flask_login.login_required]
    view_name = "forecast-model-list"
    view_url = "/forecast-models"

    def post(self):
        """Generate a new forecast model."""
        # Use `quick_init` so we don't generate the dataframe until the subprocess
        new_model = ForecastModel(quick_init=True)
        new_model.save()
        print(f"Starting model {new_model.creation_date}")
        # NOTE: For testing, send 'mock' as a parameter to avoid lengthy training
        # TODO: This is a hacky way to do this.
        if request.values.get("mock") == "true":
            process = Process(target=time.sleep, args=(3,))
        else:
            process = Process(
                target=new_model.launch_subprocess, args=(current_app.config["NAME"],)
            )
        process.start()
        new_model.store_process_id(process.pid)
        safe_flash("Model has begun training.", "info")
        return redirect(url_for("forecast-model-list"))

    def get(self):
        """Render the list of all forecast models and show the state of all data views"""
        models = ForecastModel.query.order_by(desc(ForecastModel.creation_date)).all()
        data_is_prepared = {
            "Historical load data": HistoricalLoadData.is_prepared(),
            "Historical weather data": HistoricalWeatherData.is_prepared(),
            "Forecast weather data": ForecastWeatherData.is_prepared(),
        }
        model_is_prepared = ForecastModel.is_prepared(is_prepared_dict=data_is_prepared)

        return render_template(
            "forecast-model-list.html",
            models=models,
            model_is_prepared=model_is_prepared,
            data_is_prepared=data_is_prepared,
        )


class DownloadModelFiles(MethodView):
    """View for downloading the model files"""

    view_url = "/forecast-models/<slug>/output/<path:filename>"
    view_name = "download-model-files"
    decorators = [flask_login.login_required]

    def get(self, slug, filename):
        """Expose the model's output directory to the user and return a 404 if that file doesn't exist"""
        model = ForecastModel.query.filter_by(slug=slug).first()
        rel_path = os.path.join(model.output_dir, filename)
        if model and os.path.exists(rel_path):
            # NOTE: The absolute path is necessary to make file downloadable
            abs_dir_path = os.path.abspath(model.output_dir)
            return send_from_directory(abs_dir_path, filename, as_attachment=True)
        else:
            return render_template("404.html", title="404"), 404


class ForecastModelDetailView(MethodView):
    """View for the details of a single forecast model"""

    view_name = "forecast-model-detail"
    view_url = "/forecast-models/<slug>"
    decorators = [flask_login.login_required]

    def post(self, slug):
        """Cancel a specific model"""
        model = ForecastModel.query.filter_by(slug=slug).first()
        if model.is_running:
            model.cancel()
            safe_flash(f"Model {model.slug} was cancelled.", "info")
        return redirect(url_for("forecast-model-list"))

    def get_training_chart(self, df):
        if df is None or ("forecasted_load" not in df.columns):
            return None

        df = df.sort_values("timestamp")
        load_data = [[row.timestamp, row.load] for row in df.itertuples()]
        forecast_data = [
            [row.timestamp, row.forecasted_load] for row in df.itertuples()
        ]
        return [
            {
                "data": load_data,
                "name": "Load",
            },
            {
                "data": forecast_data,
                "name": "Forecast",
                "color": "blue",
            },
        ]

    def get_forecast_chart(self, df):
        if df is None or ("forecasted_load" not in df.columns):
            return None

        df = df.sort_values("timestamp")
        # Get end of load data
        lvi = df["load"].last_valid_index()
        CONTEXT = 72
        context_data = [
            [row.timestamp, row.load]
            for row in df.iloc[lvi - CONTEXT : lvi].itertuples()
        ]
        forecast_data = [
            [row.timestamp, row.forecasted_load]
            # lvi - 1 because it's nicer to see the chart connected to historical data
            for row in df.iloc[lvi - 1 :].itertuples()
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

    def get_highest_monthly_peak(self, df, model):
        """Get the peak load for the month"""
        if model is None:
            return None
        if df is None or ("forecasted_load" not in df.columns):
            return None

        # Return none if the start date is the first of the month
        #  (otherwise we'd have to handle truthy NaNs in the logic below)
        if model.start_date.day == 1:
            return None

        month_id = f"{model.start_date.year}-{model.start_date.month}"
        df = df.set_index("dates", drop=False)
        return df.loc[month_id].load.max()

    def get(self, slug):
        forecast_model = ForecastModel.query.filter_by(slug=slug).first()

        # NOTE: Easier to just munge one dataframe for all queries
        #  more efficient to request dataframe once
        if forecast_model:
            df = forecast_model.get_df()
            df["timestamp"] = df.dates.apply(lambda x: x.timestamp() * 1000)
        else:
            df = None

        return render_template(
            "forecast-model-detail.html",
            name="forecast",
            forecast_chart=self.get_forecast_chart(df),
            training_chart=self.get_training_chart(df),
            peak_info=burtcoppd.get_on_and_off_peak_info(df, forecast_model),
            forecast_model=forecast_model,
        )


class DataSync(MethodView):
    """Abstract view to handle data syncing with external APIs."""

    view_name = None
    view_url = None
    endpoint_class = None
    parent_view = None

    def post(self):
        """Sync data with the given external API."""

        request = self.build_request()
        request.send_request()
        df = request.create_df()
        self.parent_view.model.load_df(df)
        return redirect(url_for(self.parent_view.view_name))

    def get(self):
        """Redirect any GET requests to the parent view."""

        return redirect(url_for(self.parent_view.view_name))


class HistoricalWeatherDataSync(DataSync):
    """View to sync historical weather data with the ASOS API."""

    view_name = "historical-weather-data-sync"
    view_url = "/historical-weather-data/sync"
    endpoint_class = AsosRequest
    parent_view = HistoricalWeatherDataView

    def build_request(self):
        """Given the state of the database, prepare (but don't send) an appropriate request for ASOS."""

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
    """View to sync forecast weather data with the NWS API."""

    view_name = "forecast-weather-data-sync"
    view_url = "/forecast-weather-data/sync"
    endpoint_class = NwsForecastRequest
    parent_view = ForecastWeatherDataView

    def build_request(self):
        """Given app config, prepare (but don't send) an appropriate request for NWS."""
        return NwsForecastRequest(nws_code=current_app.config["NWS_CODE"])
