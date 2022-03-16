"""
A utility to generate static pages from the forecast app. There are many hacks
in this file, but further investment wasn't deemed appropriate. 
"""

import os
import shutil

import bs4
from flask_frozen import Freezer

from forecast_app import create_app, views

# Remove login permissions from all views
views.ForecastWeatherDataView.decorators = []
views.HistoricalLoadDataView.decorators = []
views.HistoricalWeatherDataView.decorators = []
views.LatestForecastView.decorators = []
views.RenderTemplateView.decorators = []
views.ForecastModelListView.decorators = []
views.ForecastModelDetailView.decorators = []

app = create_app("demo")

freezer = Freezer(app, with_no_argument_rules=False)


@freezer.register_generator
def url_generator():
    yield "/forecast-weather-data"
    yield "/historical-load-data"
    yield "/historical-weather-data"
    yield "/latest-forecast"
    yield "/logout"
    yield "/instructions"


def insert_banner(page_path):
    """Insert a banner at the top of the page to warn users about lack of functionality."""
    with open(page_path) as f:
        soup = bs4.BeautifulSoup(f.read(), features="html.parser")

    alert = soup.new_tag("div")
    alert["class"] = "alert alert-danger"
    alert.string = "⚠️ This is a read-only static site for display purposes only. Most functionality is not available. ⚠️"
    insert_point = soup.find("div", {"class": "container-fluid"})
    insert_point.insert(0, alert)

    with open(page_path, "w") as f:
        f.write(str(soup))


if __name__ == "__main__":
    # HACK: Freezer fails, but we need what it's output before failing
    try:
        freezer.freeze()
    except Exception as e:
        pass

    demo_dir = app.config["FREEZER_DESTINATION"]

    # HACK: Add .html to all files
    os.chdir("forecast_app")
    for file in os.listdir(demo_dir):
        path = os.path.join(demo_dir, file)
        if os.path.isfile(path) and "." not in file:
            new_name = path + ".html"
            os.rename(path, new_name)

    # HACK: Set index page to the latest forecast
    latest_forecast_path = os.path.join(demo_dir, "latest-forecast.html")
    login_path = os.path.join(demo_dir, "index.html")
    shutil.copyfile(latest_forecast_path, login_path)

    # HACK: Insert alert at the top of the page
    all_pages = [
        "latest-forecast.html",
        "forecast-weather-data.html",
        "historical-load-data.html",
        "historical-weather-data.html",
        "forecast-models.html",
        "index.html",
        "instructions.html",
    ]
    for page in all_pages:
        page_path = os.path.join(demo_dir, page)
        insert_banner(page_path)
