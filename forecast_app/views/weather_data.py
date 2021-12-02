import pandas as pd
from flask import render_template
from flask.views import View

from forecast_app.utils import transform_timeseries_df_for_highcharts


class WeatherDataView(View):
    def dispatch_request(self):
        # Get historical data
        historical_df = pd.read_csv(
            "forecast_app/static/test-data/ercot-ncent-weather.csv",
            parse_dates=["timestamp"],
        )

        forecast_df = pd.read_csv(
            "forecast_app/static/test-data/mock-forecast-weather.csv",
            parse_dates=["timestamp"],
        )

        return render_template(
            "weather-data.html",
            **{
                "name": "weather-data",
                "tables": [
                    forecast_df.to_dict("records"),
                    historical_df.to_dict("records"),
                ],
                "forecast_chart": transform_timeseries_df_for_highcharts(
                    forecast_df, value="tempc"
                ),
                "historical_chart": transform_timeseries_df_for_highcharts(
                    historical_df, value="tempc"
                ),
            }
        )
