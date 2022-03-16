import os

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
# for view in dir(views):
#     if hasattr(getattr(views, view), "decorators"):
#         getattr(views, view).decorators = []

freezer = Freezer(app, with_no_argument_rules=False)


@freezer.register_generator
def url_generator():
    from forecast_app.models import ForecastModel

    yield "/"
    yield "/forecast-weather-data"
    yield "/historical-load-data"
    yield "/historical-weather-data"
    yield "/latest-forecast"
    yield "/logout"
    yield "/instructions"

    # for model in ForecastModel.query.all():
    #     yield f"/forecast-models/{model.slug}"

    # yield "/forecast-models"


if __name__ == "__main__":
    # freezer.freeze()

    # HACK: Add .html to all files
    os.chdir("forecast_app")
    for file in os.listdir(app.config["FREEZER_DESTINATION"]):
        path = os.path.join(app.config["FREEZER_DESTINATION"], file)
        if os.path.isfile(path) and "." not in file:
            new_name = path + ".html"
            os.rename(path, new_name)
