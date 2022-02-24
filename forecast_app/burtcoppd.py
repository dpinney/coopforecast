"""A module for burtco-specific functions that aren't easily generalizable to other utilities"""


def get_on_and_off_peak_info(df, model):
    """Given a model's dataframe, get the month's max on peak and off peak load and timestamp info"""
    if model is None:
        return None
    if df is None or ("forecasted_load" not in df.columns):
        return None

    # Return none if the start date is the first of the month
    #  (otherwise we'd have to handle truthy NaNs in the logic below)
    if model.start_date.day == 1:
        return None

    ON_PEAK_START_HOUR = 8  # "HE9", or 08-09
    ON_PEAK_END_HOUR = 21  # "HE22", or 21-22

    # First get only this month's data
    df = df.set_index("dates", drop=False)
    month_id = f"{model.start_date.year}-{model.start_date.month}"
    df = df.loc[month_id]

    # split dataframe into on peak and off peak and get max load and timestamps
    df_on_peak = df[
        (df.dates.dt.hour >= ON_PEAK_START_HOUR)
        & (df.dates.dt.hour <= ON_PEAK_END_HOUR)
    ]
    df_off_peak = df[~df.dates.isin(df_on_peak.dates)]
    return {
        "on_peak": {
            "max_load": df_on_peak.load.max(),
            "timestamp": df_on_peak.load.idxmax(),
        },
        "off_peak": {
            "max_load": df_off_peak.load.max(),
            "timestamp": df_off_peak.load.idxmax(),
        },
    }
