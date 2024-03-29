import datetime
import os
import shutil
from subprocess import Popen
from urllib.parse import urljoin

import pandas as pd
import requests
import typer

import forecast_app.forecast as lf
from forecast_app import create_app
from forecast_app.commands import init_db, upload_demo_data
from forecast_app.config import config_map
from forecast_app.models import (
    ForecastModel,
    ForecastWeatherData,
    HistoricalLoadData,
    HistoricalWeatherData,
)
from forecast_app.tests.test_weather import TestAsosRequest, TestNwsForecastRequest

typer_app = typer.Typer()


@typer_app.command()
def restart_db(config: str = "dev"):
    """Restart with a blank database."""
    # NOTE: Because of lazy loading, restarting db and uploading demo data cannot be
    #  included as options in deploy()
    app = create_app(config)
    with app.app_context():
        if os.path.exists(app.config["SQLALCHEMY_DATABASE_URI"]):
            all_models = ForecastModel.query.all()
            for model in all_models:
                model.delete()
        init_db()


@typer_app.command()
def demo(config: str = "dev"):
    """Restart with a demo database."""
    # NOTE: Because of lazy loading, restarting db and uploading demo data cannot be
    #  included as options in deploy()
    app = create_app(config)
    with app.app_context():
        if os.path.exists(app.config["SQLALCHEMY_DATABASE_URI"]):
            all_models = ForecastModel.query.all()
            for model in all_models:
                model.delete()
        init_db()
        upload_demo_data()


@typer_app.command()
def deploy(
    config: str = "dev", no_gunicorn: bool = typer.Option(False, "--no-gunicorn")
):
    """Launch the app"""

    config_class = config_map.get(config)
    if not config_class:
        raise ValueError("Invalid config")

    if no_gunicorn:
        app = create_app(config)
        app.run(debug=config_class.DEBUG, host="0.0.0.0", port=config_class.PORT)
    else:
        Popen(
            [
                config_class.GUNICORN_PATH,
                f"--bind=0.0.0.0:{config_class.REDIRECT_PORT}",
                "redirect:reApp",
            ]
        )
        # Start application:
        appProc = [
            config_class.GUNICORN_PATH,
            f"--workers={config_class.WORKERS}",
            f"--bind=0.0.0.0:{config_class.PORT}",
            f"forecast_app:create_app('{config_class.NAME}')",
        ]
        if config == "dev":
            appProc.append("--reload")  # NOTE: This doesn't seem to be working.
        if config == "prod":
            appProc += [
                f"--certfile={config_class.CERT_DIR}/cert.pem",
                f"--ca-certs={config_class.CERT_DIR}/fullchain.pem",
                f"--keyfile={config_class.CERT_DIR}/privkey.pem",
                "--error-logfile=forecaster.error.log",
                "--capture-output",
                "--access-logfile=forecaster.access.log",
                "--preload",  # NOTE: This is incompatible with --reload
            ]
        Popen(appProc).wait()


@typer_app.command()
def test_apis():
    """Query the ASOS API without a mock to ensure that it works as intended."""
    TestAsosRequest.test_asos_api()
    print("ASOS API test passed.")
    TestNwsForecastRequest.test_nws_api()
    print("NWS API test passed.")


def create_login_session(username, password, base_url):
    session = requests.Session()
    # Login to the site
    response = session.post(
        urljoin(base_url, "/"), data={"username": username, "password": password}
    )
    assert response.status_code == 200, "Login failed."
    return session


@typer_app.command()
def post_data(
    filepath: str,
    BASE_URL: str = typer.Option("http://localhost:5000", "--url"),
    type: str = typer.Option(
        "historical-load",
        "--type",
        help="Choices are `forecast-weather`, `historical-weather`, or `historical-load`",
    ),
    username: str = typer.Option("admin", "--username"),
    password: str = typer.Option("admin", "--password"),
):
    """Post historical or forecast data to the site in lieu of going through the UI."""

    session = create_login_session(username, password, BASE_URL)

    # Upload data from the session
    files = {"file": open(filepath, "rb")}

    # /forecast-load-data can handle both weather or load data, so we can simplify
    #  the cli and just intuiting what the user needs via the file they upload.
    endpoint_map = {
        "forecast-weather": "/forecast-weather-data",
        "historical-weather": "/historical-weather-data",
        "historical-load": "/historical-load-data",
    }
    if type not in endpoint_map:
        raise ValueError(f"Invalid data type: {type}. See --help for options.")

    response = session.post(urljoin(BASE_URL, endpoint_map[type]), files=files)
    assert (
        response.status_code == 302  # HACK: Status code is redirect if successful
    ), f"Upload failed. Status code: {response.status_code}"


@typer_app.command()
def backup(
    export_dir: str = typer.Option(
        "backup", "--export-dir", help="Where should the data be exported?"
    ),
    config: str = "dev",
):
    """Export historical and forecast data to csv."""
    export_id = datetime.datetime.now().strftime("%Y-%m-%d.%H-%M-%S")
    app = create_app(config)

    export_dir = os.path.join(export_dir, str(export_id))
    os.makedirs(export_dir)

    # BACKUP TRAINING DATA
    historical_load_path = os.path.join(export_dir, f"historical-load-{export_id}.csv")
    historical_temp_path = os.path.join(export_dir, f"historical-temp-{export_id}.csv")
    forecast_temp_path = os.path.join(export_dir, f"forecast-temp-data-{export_id}.csv")
    with app.app_context():
        HistoricalLoadData.to_df().to_csv(historical_load_path, index=False)
        HistoricalWeatherData.to_df().to_csv(historical_temp_path, index=False)
        ForecastWeatherData.to_df().to_csv(forecast_temp_path, index=False)

    # BACKUP DB
    local_db = app.config["SQLALCHEMY_DATABASE_URI"].split("///")[1]
    # TODO: If db is not stored locally, this won't work.
    db_path = os.path.join("forecast_app", local_db)
    backup_db_path = os.path.join(
        export_dir, f"{local_db.split('/')[-1]}-{export_id}.db"
    )
    shutil.copyfile(db_path, backup_db_path)

    # TODO: BACKUP MODELS


@typer_app.command()
def remove_old_models(
    config: str = "dev",
    days: int = typer.Option(
        30, "--days", help="How many days of models should be kept?"
    ),
    assume_yes: bool = typer.Option(
        False, "--assume-yes", help="Assume yes to delete confirmation."
    ),
    model_minimum: int = typer.Option(
        20,
        "--model-minimum",
        help="Don't delete anything if there are fewer than this number of models.",
    ),
):
    """Remove models older than a certain number of days."""
    app = create_app(config)
    with app.app_context():
        # First confirm that there are too many models.
        model_count = len(ForecastModel.query.all())
        if model_count < model_minimum:
            print(
                f"There are only {model_count} models. This is fewer than the model minimum of {model_minimum}. Not deleting."
            )
            return

        # Get the old models and delete if there are any and the user confirms, abort otherwise.
        old_models = ForecastModel.query.filter(
            ForecastModel.creation_date
            < datetime.datetime.now() - datetime.timedelta(days=days)
        ).all()

        if len(old_models) == 0:
            print(f"No models are older than {days} days.")
            return

        if assume_yes or typer.confirm(
            f"Are you sure you want to delete {len(old_models)} models?", abort=True
        ):
            for model in old_models:
                model.delete()


@typer_app.command()
def shell(config: str = "dev"):
    """Launch pdb shell in the app context with common imports"""
    app = create_app(config)
    with app.app_context():
        # Launch pdb
        breakpoint()


@typer_app.command()
def sync_weather_data(
    BASE_URL: str = typer.Option("http://localhost:5000", "--url"),
    username: str = typer.Option("admin", "--username"),
    password: str = typer.Option("admin", "--password"),
):
    """Sync weather data from ASOS and NWS"""
    session = create_login_session(username, password, BASE_URL)
    print("Syncing historical weather data...")
    session.post(urljoin(BASE_URL, "/historical-weather-data/sync"))
    print("Historical weather data completed ✓")
    print("Syncing forecast weather data...")
    session.post(urljoin(BASE_URL, "/forecast-weather-data/sync"))
    print("Forecast weather data completed ✓")


@typer_app.command()
def launch_new_model(
    BASE_URL: str = typer.Option("http://localhost:5000", "--url"),
    username: str = typer.Option("admin", "--username"),
    password: str = typer.Option("admin", "--password"),
):
    """Generate a new model"""
    session = create_login_session(username, password, BASE_URL)
    print("Posting request to launch new model...")
    session.post(urljoin(BASE_URL, "/forecast-models"))
    print("Forecast model has begun training ✓")


@typer_app.command()
def test_forecaster(
    num_tests: int = typer.Option(1, "--num-tests"),
    epochs: int = typer.Option(1, "--epochs"),
):
    """Test forecaster from command line, useful for iterating on the model"""

    # Here "utility-cached-dataframe.csv" is the latest data available from the utility
    #  as output from the site. This private data can help us iterate on improving
    #  the model.
    df = pd.read_csv("~/utility-cached-dataframe.csv", parse_dates=["dates"])
    data_split = lf.DataSplit(df)

    accuracies = []
    for _ in range(num_tests):
        model, accuracy = lf.train_and_test_model(
            data_split, epochs=epochs, tensorboard=True
        )
        accuracies.append(accuracy)
        print(
            f"Epochs: {epochs},  Train: {accuracy['train']}, Test: {accuracy['test']}"
        )

    if num_tests > 1:
        print(f"Epochs: {epochs}")
        train_accuracies = [acc["train"] for acc in accuracies]
        print("Average test accuracy:", sum(train_accuracies) / len(train_accuracies))
        test_accuracies = [acc["test"] for acc in accuracies]
        print(
            f"Average training accuracy: {sum(test_accuracies) / len(test_accuracies)}"
        )


if __name__ == "__main__":
    typer_app()
