import typer
from subprocess import Popen
from forecast_app import create_app
from forecast_app.commands import init_db, upload_demo_data
from forecast_app.config import config_map

typer_app = typer.Typer()

# NOTE: Currently only configured for development config.
# - Because of lazy loading, restarting db and uploading demo data cannot be
#  included as options in launch()


@typer_app.command()
def restart_db(config: str = "dev"):
    """Restart with a blank database."""
    app = create_app(config)
    with app.app_context():
        init_db()


@typer_app.command()
def demo(config: str = "dev"):
    """Restart with a demo database."""
    app = create_app(config)
    with app.app_context():
        init_db()
        upload_demo_data()


@typer_app.command()
def launch(config: str = "dev"):
    app = create_app(config)
    app.run(debug=True, host="0.0.0.0", port=5000)


@typer_app.command()
def deploy(config: str = "dev"):
    # TODO: Implement HTTPS redirection
    # redirProc = Popen(["gunicorn", "-w", "5", "-b", "0.0.0.0:80", "webProd:reApp"])
    # TODO: Combine logging: https://www.linkedin.com/pulse/logs-flask-gunicorn-pedro-henrique-schleder/

    config_class = config_map.get(config)
    if not config_class:
        raise ValueError("Invalid config")

    # Start application:
    appProc = [
        "gunicorn",
        "--workers=5",  # TODO: Configure number of workers from app config.
        f"--bind=0.0.0.0:{config_class.PORT}",
        f"forecast_app:create_app('{config_class.NAME}')",
        # "--certfile=omfDevCert.pem",  # SSL certificate file
        # "--ca-certs=certChain.ca-bundle",  # CA certificates file
        # "--keyfile=omfDevKey.pem",  # SSL key file
    ]
    if config == "dev":
        appProc.append("--reload")  # NOTE: This doesn't seem to be working.
    if config == "prod":
        appProc += [
            "--error-logfile=forecaster.error.log",
            "--capture-output",
            "--access-logfile=forecaster.access.log",
            "--preload",  # NOTE: This is incompatible with --reload
        ]
    Popen(appProc).wait()


if __name__ == "__main__":
    typer_app()
