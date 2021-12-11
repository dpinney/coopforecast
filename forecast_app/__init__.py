from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy

from forecast_app.utils import RenderTemplateView
from forecast_app.views import LoadDataView, WeatherDataView, ForecastView
from forecast_app.db import session, init_db_command
from forecast_app.commands import upload_demo_data

import os
from flask import Flask, flash, request, redirect, url_for
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"csv"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def create_app():
    app = Flask(__name__)

    app.config["UPLOAD_FOLDER"] = "forecast_app/static/uploads"
    app.config["SECRET_KEY"] = "super secret key"

    app.add_url_rule("/", view_func=RenderTemplateView.view("login"))
    app.add_url_rule("/load-data", view_func=LoadDataView.as_view("load-data"))

    @app.route("/load-data", methods=["POST"])
    def upload_file():
        if request.method == "POST":
            # check if the post request has the file part
            if "file" not in request.files:
                flash("No file part")
                return redirect(request.url)
            file = request.files["file"]
            # If the user does not select a file, the browser submits an
            # empty file without a filename.
            if file.filename == "":
                flash("No selected file")
                return redirect(request.url)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                return """
                    <!doctype html>
                    <h1> Congrats! You have successfully uploaded your file!</h1>
                    """
        return """
        <!doctype html>
        <title>Upload new File</title>
        <h1>Upload new File</h1>
        
        """

    app.add_url_rule("/weather-data", view_func=WeatherDataView.as_view("weather-data"))
    app.add_url_rule("/instructions", view_func=RenderTemplateView.view("instructions"))
    app.add_url_rule("/forecast", view_func=ForecastView.as_view("forecast"))
    app.add_url_rule(
        "/model-settings", view_func=RenderTemplateView.view("model-settings")
    )
    app.add_url_rule(
        "/user-settings", view_func=RenderTemplateView.view("user-settings")
    )

    app.cli.add_command(init_db_command)
    app.cli.add_command(upload_demo_data)

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        session.remove()

    return app
