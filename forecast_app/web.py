from flask import Flask, render_template, url_for

app = Flask(__name__)


@app.route("/")
def login():
    return render_template("login.html", name="login")
    # return "Hello World!"


@app.route("/load-data")
def load_data():
    return render_template("load-data.html", name="load-data")


@app.route("/weather-data")
def weather_data():
    return render_template("weather-data.html", name="weather-data")


@app.route("/forecast")
def forecast():
    return render_template("forecast.html", name="forecast")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=1546)
