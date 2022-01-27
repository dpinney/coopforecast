"""
A collection of utilities to help collect and parse historical and forecast weather data.
"""

import requests
from io import StringIO
import pandas as pd


class AsosRequest:
    """Pulls hourly data for a specified year and ASOS station. Drawn heavily from
    https://github.com/dpinney/omf
    * ASOS is the Automated Surface Observing System, a network of about 900
            weater stations, they collect data at hourly intervals, they're run by
            NWS, FAA, and DOD, and there is data going back to 1901 in some sites.
    * AKA METAR data, which is the name of the format its stored in.
    * For ASOS station code see https://www.faa.gov/air_traffic/weather/asos/
    * For datatypes see bottom of https://mesonet.agron.iastate.edu/request/download.phtml
    * Note for USA stations (beginning with a K) you must NOT include the 'K'
    * ASOS User's Guide: https://www.weather.gov/media/asos/aum-toc.pdf
    """

    base_url = "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py"

    def __init__(
        self, start_date=None, end_date=None, station=None, tz=None, missing_value="M"
    ):
        self.start_date = start_date
        self.end_date = end_date
        self.station = station
        self.tz = tz
        self.missing_value = missing_value
        self.params = {
            "station": station,
            "data": "tmpc",
            "year1": start_date.year,
            "month1": start_date.month,
            "day1": start_date.day,
            "year2": end_date.year,
            "month2": end_date.month,
            "day2": end_date.day,
            "tz": tz,
            "format": "onlycomma",
            "missing": missing_value,
            "trace": "T",  # What does this mean?
            "latlon": "no",
            "elev": "no",
            "direct": "no",
            "report_type": 1,
            "report_type": 2,  # Why?
        }

    def send_request(self):
        self.request = requests.get(self.base_url, params=self.params)
        if self.request.status_code == 404:
            raise Exception(f"Dataset URL does not exist. {self.request.url}")
        return self.request

    def write_response(self, filepath):
        self.filepath = filepath
        if getattr(self, "request", None) is None:
            raise Exception("No request has been sent yet.")
        if not self.request.text:
            raise Exception(f"No data found. {self.request.url}")
        with open(filepath, "w") as f:
            f.write(self.request.text)

    def create_df(self):
        if getattr(self, "request", None) is None:
            raise Exception("No request has been sent yet.")
        df = pd.read_csv(
            StringIO(self.request.text), parse_dates=["valid"], index_col="valid"
        )
        df = df[df["tmpc"] != self.missing_value]
        df["tmpc"] = df["tmpc"].astype(float)
        return df

    @classmethod
    def round_hours(df):
        """Given a dataframe of temperature data from asos, collect times to the nearest hour."""
        # TODO: Set valid as index, interpolate and resample to nearest hour
        return df.groupby(pd.Grouper(freq="H"))


# def int_climate():
#     fname = "tekamah_hist_temp.csv"
#     x = pd.read_csv(fname)
#     print(x)
#     y = x.interpolate()
#     print(y)
#     y["dt_index"] = pd.to_datetime(y["valid"])
#     z = y.set_index("dt_index")
#     print(z)
#     w = z.resample("h").mean()
#     print(w)
#     v.to_csv("tekamah_hist_temp_hourly.csv")


# Given a start datetime and a zipcode, collect the next 24 hours of forecasted temperature data.
