"""
A collection of utilities to help collect and parse historical and forecast weather data.
"""

import requests
from io import StringIO
import pandas as pd
import json


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

    # TODO: The user should be able to access the request url before sending the request
    #  both this and the Nws API should be changed

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
        if not hasattr(self, "request"):
            raise Exception("No request has been sent yet.")
        if not self.request.text:
            raise Exception(f"No data found. {self.request.url}")
        with open(filepath, "w") as f:
            f.write(self.request.text)

    def create_df(self):
        if not hasattr(self, "request"):
            raise Exception("No request has been sent yet.")
        df = pd.read_csv(StringIO(self.request.text), parse_dates=["valid"])
        df = df[df["tmpc"] != self.missing_value]
        df["tempc"] = df["tmpc"].astype(float)  # rename column and cast
        df["timestamp"] = df.valid.dt.round("h")  # Round to nearest hour
        df = df[["timestamp", "tempc"]]
        series = df.groupby("timestamp")["tempc"].mean()

        # Cast as a dataframe and ensure a continuous index
        df_n = pd.DataFrame(series)
        df_n = df_n.resample("h").last()
        df_n["timestamp"] = df_n.index
        return df_n


class NwsForecastRequest:
    # TODO: Can this be an abstract class?
    """Pulls hourly data from the National Weather Service
    Docs: https://weather-gov.github.io/api/
    Example request: https://api.weather.gov/gridpoints/LWX/96,70/forecast/hourly
    * Timezone data is encoded in the response as UTC with offset. We strip it.
    * The temperature is in Fahrenheit, we convert to Celsius.
    * 6.5 days of forecast data is provided.
    """

    base_url = "https://api.weather.gov/gridpoints/"

    def __init__(self, nws_code=""):
        self.nws_code = nws_code

    @classmethod
    def fahrenheit_to_celcius(cls, fahrenheit):
        # TODO: We should be using fahrenheit instead of celcius, but it's baked into
        #  a lot of the structure. May not be worth switching back for a while.
        return round((fahrenheit - 32) * 5 / 9, 2)

    def send_request(self):
        self.request = requests.get(self.base_url + self.nws_code + "/forecast/hourly")
        if self.request.status_code == 404:
            raise Exception(f"Dataset URL does not exist. {self.request.url}")
        return self.request

    def write_response(self, filepath):
        self.filepath = filepath
        if not hasattr(self, "request"):
            raise Exception("No request has been sent yet.")
        if not self.request.text:
            raise Exception(f"No data found. {self.request.url}")
        with open(filepath, "w") as f:
            f.write(self.request.text)

    def create_df(self):
        if not hasattr(self, "request"):
            raise Exception("No request has been sent yet.")
        json_response = json.loads(self.request.text)
        dict_list = []
        for item in json_response["properties"]["periods"]:
            item = {
                # Removing tz info from timestamp. This makes the strong assumption
                #  that NWS will always correctly provide data in the timezone of
                #  the station we're pulling from.
                "timestamp": pd.to_datetime(item["startTime"]).replace(tzinfo=None),
                "tempc": self.fahrenheit_to_celcius(item["temperature"]),
            }
            dict_list.append(item)
        df = pd.DataFrame(dict_list)

        return df
