from flask import request, flash, current_app
from werkzeug.utils import secure_filename
import os
from flask_executor import Executor
from flask_login import LoginManager, UserMixin
from flask_sqlalchemy import SQLAlchemy

import pandas as pd

executor = Executor()
db = SQLAlchemy()

# SETUP LOGIN MANAGER ---------------------------------------------------------
# https://flask-login.readthedocs.io/en/latest/
# Currently only supporting one user. flask-login requires user_loader and
#  request_loader to be implemented. Username and password set in
#  config.py / secret_config.py

login_manager = LoginManager()
ADMIN_USER = UserMixin()


@login_manager.user_loader
def user_loader(username):
    if username != ADMIN_USER.id:
        return
    return ADMIN_USER


@login_manager.request_loader
def request_loader(request):
    if request.form.get("username") != ADMIN_USER.id:
        return
    ADMIN_USER.is_authenticated = (
        request.form["password"] == current_app.config["ADMIN_PASSWORD"]
    )
    return ADMIN_USER


# -----------------------------------------------------------------------------


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
