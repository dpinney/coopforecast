import typer
from subprocess import Popen
from forecast_app import create_app
from forecast_app.commands import init_db, upload_demo_data
from forecast_app.config import config_map
from forecast_app.tests.test_weather import test_asos_api

typer_app = typer.Typer()


@typer_app.command()
def restart_db(config: str = "dev"):
    """Restart with a blank database."""
    # NOTE: Because of lazy loading, restarting db and uploading demo data cannot be
    #  included as options in deploy()
    app = create_app(config)
    with app.app_context():
        init_db()


@typer_app.command()
def demo(config: str = "dev"):
    """Restart with a demo database."""
    # NOTE: Because of lazy loading, restarting db and uploading demo data cannot be
    #  included as options in deploy()
    app = create_app(config)
    with app.app_context():
        init_db()
        upload_demo_data()


@typer_app.command()
def deploy(
    config: str = "dev", no_gunicorn: bool = typer.Option(False, "--no-gunicorn")
):
    # TODO: Combine logging: https://www.linkedin.com/pulse/logs-flask-gunicorn-pedro-henrique-schleder/

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
def test_asos():
    """Query the ASOS API without a mock to ensure that it works as intended."""
    test_asos_api()


if __name__ == "__main__":
    typer_app()
