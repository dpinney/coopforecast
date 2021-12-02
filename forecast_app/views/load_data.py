import pandas as pd
from flask import Flask, render_template, url_for

from forecast_app.lib.utils import transform_timeseries_df_for_highcharts


class LoadDataView:
    def __init__(self):
        self.df = self.get_data()

    def get_data(self):
        return pd.read_csv(
            "forecast_app/static/test-data/ercot-ncent-load.csv",
            parse_dates=["timestamp"],
        )

    def get_table(self):
        return self.df.to_dict("records")

    def get_chart(self):
        return transform_timeseries_df_for_highcharts(self.df, value="load")

    def render(self):
        return render_template(
            "load-data.html",
            **{
                "name": "load-data",
                "table": self.get_table(),
                "chart": self.get_chart(),
            }
        )
