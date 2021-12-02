import pandas as pd
from flask import render_template
from flask.views import View

from forecast_app.utils import transform_timeseries_df_for_highcharts


class LoadDataView(View):
    def __init__(self, *args, **kwargs):
        self.df = pd.read_csv(
            "forecast_app/static/test-data/ercot-ncent-load.csv",
            parse_dates=["timestamp"],
        )
        super().__init__()

    def get_table(self):
        return self.df.to_dict("records")

    def get_chart(self):
        return transform_timeseries_df_for_highcharts(self.df, value="load")

    def dispatch_request(self):
        return render_template(
            "load-data.html",
            **{
                "name": "load-data",
                "table": self.get_table(),
                "chart": self.get_chart(),
            }
        )


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


class ForecastView(View):
    def dispatch_request(self):
        df = pd.read_csv(
            "forecast_app/static/test-data/mock-forecast-load.csv",
            parse_dates=["timestamp"],
        )

        return render_template(
            "forecast.html",
            name="forecast",
            chart=transform_timeseries_df_for_highcharts(df, value="load"),
        )
