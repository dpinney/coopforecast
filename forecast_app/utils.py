"""Collection of utility functions, db configurations, and authentication."""
import os
import logging
import pandas as pd

from flask import request, flash, current_app, has_request_context
from werkzeug.utils import secure_filename
from flask_login import LoginManager, UserMixin
from flask_sqlalchemy import SQLAlchemy

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
    """Return the authenticated. We only have one. Configuring this is required by flask-login."""
    if username != ADMIN_USER.id:
        return
    return ADMIN_USER


@login_manager.request_loader
def request_loader(request):
    """Ensure that user is authenticated. Configuring this is required for flask-login."""

    if request.form.get("username") != ADMIN_USER.id:
        return
    ADMIN_USER.is_authenticated = (
        request.form["password"] == current_app.config["ADMIN_PASSWORD"]
    )
    return ADMIN_USER


# -----------------------------------------------------------------------------


def allowed_file(filename):
    """Return true if the file is an allowed filetype."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ["csv", "xlsx"]


def upload_file(name):
    """In a request context, upload a file to the upload directory."""
    # check if the post request has the file part
    if name not in request.files:
        safe_flash("Cannot find a file with that name", "danger")
        return None
    file = request.files[name]
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == "":
        safe_flash("No selected file", "danger")
        return None
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config["UPLOAD_DIR"], filename)
        file.save(filepath)
        return filepath


def safe_error(error_message):
    """Raise an error if in debug mode, otherwise flash error message in the UI."""
    if not has_request_context() or current_app.config["DEBUG"]:
        raise Exception(error_message)
    else:
        flash(error_message, "danger")


def safe_flash(message, category):
    """Only allow flash to be called in a request context."""
    categories = {
        "info": logging.INFO,
        "success": logging.INFO,
        "warning": logging.WARNING,
        "danger": logging.ERROR,
    }
    assert category in categories

    if category == "danger":
        safe_error(message)
    else:
        if not has_request_context():
            logging.log(msg=message, level=categories[category])
        else:
            flash(message, category)
