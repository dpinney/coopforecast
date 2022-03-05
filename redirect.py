"""
Small redirect app to redirect HTTP traffic to HTTPS.
See CLI for usage and configuration
"""

from flask import Flask, redirect, request

reApp = Flask("HTTPS_REDIRECT")


@reApp.route("/")
def index():
    return "NA"


@reApp.before_request
def before_request():
    if request.url.startswith("http://"):
        url = request.url.replace("http://", "https://", 1)
        return redirect(url, code=301)
