"""
A collection of utilities to help collect and parse historical and forecast weather data.
"""

import requests
from datetime import date
from io import StringIO
import pandas as pd

# Given two datetimes and a zipcode, return all temperature data between them.
def pull_asos(start_date=None, end_date=None, station=None, tz=None):
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
    MISSING_VALUE = "M"

    base_url = "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py"
    params = {
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
        "missing": MISSING_VALUE,
        "trace": "T",  # What does this mean?
        "latlon": "no",
        "elev": "no",
        "direct": "no",
        "report_type": 1,
        "report_type": 2,  # Why?
    }

    request = requests.get(base_url, params=params)
    if request.status_code == 404:
        raise Exception(f"Dataset URL does not exist. {request.url}")

    df = pd.read_csv(StringIO(request.text), parse_dates=["valid"])
    if df.empty:
        raise Exception(f"No data found for that zipcode. {request.url}")
    df = df[df["tmpc"] != MISSING_VALUE]
    df["tmpc"] = df["tmpc"].astype(float)
    return df  # NOTE: "tmpc", not "tempc"


# Given a dataframe of temperature data from asos, collect times to the nearest hour.

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
#     v = w.interpolate()
#     v.to_csv("tekamah_hist_temp_hourly.csv")


# Given a start datetime and a zipcode, collect the next 24 hours of forecasted temperature data.

# Given a collection of temperature data, remove outliers.
def remove_outliers(data):
    values = [-9999]
    return []
