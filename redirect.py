"""
Small redirect app to redirect HTTP traffic to HTTPS.
See CLI for usage and configuration
"""

from flask import Flask, redirect, request, send_from_directory

reApp = Flask("HTTPS_REDIRECT")


@reApp.route("/")
def index():
    return "NA"


@reApp.before_request
def before_request():
    if '/.well-known/acme-challenge' in request.url:
        try:
            filename = request.url.split('/')[-1]
        except:
            filename = 'none'
        return send_from_directory('/opt/coopforecast/forecast_app/.well-known/acme-challenge', filename)
    elif request.url.startswith("http://"):
        url = request.url.replace("http://", "https://", 1)
        return redirect(url, code=301)
