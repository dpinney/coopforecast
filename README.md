# burtForecaster
Electric Utility Load Forecaster Application

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![run_pytest](https://github.com/dpinney/burtForecaster/actions/workflows/run_pytest.yaml/badge.svg)](https://github.com/dpinney/burtForecaster/actions/workflows/run_pytest.yaml)

## Launch with docker

```sh
docker compose up
```

And view the application at http://localhost:5000/.

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