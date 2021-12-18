from flask import render_template, request, flash, current_app, redirect
from flask.views import View
from werkzeug.utils import secure_filename
import os
from flask_executor import Executor
from flask_login import LoginManager, UserMixin, login_required

from forecast_app.models import HistoricalData, ForecastData
import pandas as pd


executor = Executor()
login_manager = LoginManager()

# TODO: Move me!
users = {
    "user1@gmail.com": {"pw": "pass1"},
    "user2@aol.com": {"pw": "pass2"},
    "user3@hotmail.com": {"pw": "pass3"},
}

# TODO: Move me!
class User(UserMixin):
    pass


@login_manager.user_loader
def user_loader(username):
    if username not in users:
        return

    user = User()
    user.id = username
    return user


@login_manager.request_loader
def request_loader(request):
    username = request.form.get("username")
    if username not in users:
        return

    user = User()
    user.id = username

    user.is_authenticated = request.form["pw"] == users[username]["pw"]

    return user


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() == "csv"


def upload_file(name):
    # check if the post request has the file part
    if "file" not in request.files:
        flash("No file part")
        return None
    file = request.files[name]
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == "":
        flash("No selected file")
        return None
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)
        return filepath


class RenderTemplateView(View):
    def __init__(self, template_name):
        self.template_name = template_name

    def dispatch_request(self):
        return render_template(self.template_name)

    @classmethod
    def view(cls, name, template=None):
        if not template:
            template = name + ".html"
        return cls.as_view(name, template_name=template)
