def transform_timeseries_df_for_highcharts(df, value=None):
    """
    Highcharts uses milliseconds, not seconds, so multiply by 1000. And
    then zip with the load value.
    """
    highcharts_array = []
    for i, row in df.iterrows():
        highcharts_array.append([row["timestamp"].timestamp() * 1000, row[value]])
    return highcharts_array
