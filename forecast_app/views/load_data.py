import pandas as pd
from flask import Flask, render_template, url_for
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
