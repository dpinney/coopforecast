# burtForecaster
Electric Utility Load Forecaster Application

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![run_pytest](https://github.com/dpinney/burtForecaster/actions/workflows/run_pytest.yaml/badge.svg)](https://github.com/dpinney/burtForecaster/actions/workflows/run_pytest.yaml)

## Application Deployment

#### Installation

1. Bring up an [Ubuntu 20.04 LTS](https://releases.ubuntu.com/20.04/) machine.
2. Configure DNS to point to new VM (needed for TLS cert creation).
3. Ensure ports 443 and 80 are open (e.g., on hosting provider's firewall).
4. Clone the repo: `git clone https://github.com/dpinney/burtForecaster` to `/opt/`
5. Copy `cp forecast_app/secret_config.py.sample forecast_app/secret_config.py` and edit all the values.
6. Export EMAIL and DOMAIN values to environment variables.
7. Run the install script `install.sh`

## Launch with docker

```sh
docker image build -t requirements .
docker compose up
```

And view the application at http://localhost:5000/.

**(M1 bug)** If you're building on M1, you'll need to build with a separate 
Docker image.

```sh
docker image build -t requirements -f Dockerfile-arm64 .
docker compose up
```

## Launch without docker

Create a python 3.8 virtual environment and download packages from `requirements.txt`:

```sh
python3.8 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

After installation, run the application by executing the run script:

```sh
python cli.py deploy --config dev
```

## Prepare database

To initialize the database and fill with data run the following commands:

```sh
# Remove existing database and create a new one
python cli.py restart-db --config dev
# Load demo data into database
python cli.py demo --config dev
```

## Development

### Install black pre-commit

In order to follow black style guidelines, simply run the following command:

```sh
pre-commit install
```

This will prevent you from committing un-styled code.