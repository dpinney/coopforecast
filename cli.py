from flask.cli import with_appcontext
import typer
from flask.cli import with_appcontext
from forecast_app import create_app
from forecast_app.config import DevelopmentConfig, ProductionConfig
from forecast_app.commands import init_db, upload_demo_data

typer_app = typer.Typer()

# NOTE: Currently only configured for development config.
# - Because of lazy loading, restarting db and uploading demo data cannot be
#  included as options in launch()

config_map = {
    "dev": DevelopmentConfig,
    "prod": ProductionConfig,
}


@typer_app.command()
def restart_db(config: str = "dev"):
    """Restart with a blank database."""
    app = create_app(config_map[config])
    with app.app_context():
        init_db()


@typer_app.command()
def demo(config: str = "dev"):
    """Restart with a demo database."""
    app = create_app(config_map[config])
    with app.app_context():
        init_db()
        upload_demo_data()


@typer_app.command()
def launch(config: str = "dev"):
    app = create_app(config_map[config])
    app.run(debug=True, host="0.0.0.0", port=5000)


if __name__ == "__main__":
    typer_app()
