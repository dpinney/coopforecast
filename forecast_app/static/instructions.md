# Instructions

- [Instructions](#instructions)
  - [Historical Load Data](#historical-load-data)
  - [Weather Data](#weather-data)
    - [Historical Data](#historical-data)
    - [Weather Forecast](#weather-forecast)
  - [Forecaster](#forecaster)
  - [Read More](#read-more)

## Historical Load Data

Upload load data via CSV. Any units can be used, but remember that the prediction will then be in those units, and then of course ensure that while inputting data, all values share the same units. Hour-by-hour load data is expected.

Two columns are expected: `timestamp` and `load`. Please use [ISO_8601](https://en.wikipedia.org/wiki/ISO_8601) formatting (`YYYY-MM-DD HH:00`). New timestamps will be added and timestamps with existing values will be overwritten.

[View an example load dataset](https://gist.github.com/kmcelwee/ce163d8c9d2871ab4c652382431c7801)

The model considers hour of day, month of year, holidays, and temperature when making its predictions. We recommended that at least 3 years of data is provided so that each of these factors can be appropriately trained.

An important note: The model must be trained on load data that reflects if no peak shaving strategy was implemented. 

Make sure to fully inspect the data. The quality of the prediction is directly a consequence of the quality of the data. Look for outliers and null values. Fill any zeros or empty values with best-guesses. A single approximate data point will not hurt the model, but a collection of absolutely wrong values could seriously hurt accuracy.

The model will predict the 24 hours following the final hour that is provided.


## Weather Data

### Historical Data

In order to ensure that the weather data can be properly collected, please first import load data for new dates before importing weather data. Weather data can be upload as a CSV or given a zipcode, a user can automatically collect temperature data. Similar to load data, ensuring the quality of weather data is very important, especially if it was collected automatically. Fill any zeros or empty values with best-guesses. A single approximate data point will not hurt the model, but a collection of absolutely wrong values could seriously hurt accuracy.

Two columns are expected: `timestamp` and `tempc`. The model and API expect users to input Celcius. Please use [ISO_8601](https://en.wikipedia.org/wiki/ISO_8601) formatting (`YYYY-MM-DD HH:00`). New timestamps will be added and timestamps with existing values will be overwritten.

[View an example historical weather dataset](https://gist.github.com/kmcelwee/e56308a8096356fcdc699ca168904aa4)

### Weather Forecast

In addition to historical data, the model requires a 24 hour forecast in order to make a prediction. This is also available as an automated process, but because the quality of the data cannot be gauranteed, we ask that you review this data before a load forecast is made.

[View an example weather forecast](https://gist.github.com/kmcelwee/071cac5e2b20c2f260f1bf7f9b3387f3)

## Forecaster

Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod
tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam,
quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo
consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse
cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non
proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

## Read More

Interested in the details of how this model works? Consider inspecting the [source code](https://www.github.com/dpinney/burtForecaster) or reading [more research.](https://www.kmcelwee.com/load-forecasting)
