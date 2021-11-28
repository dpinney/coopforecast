# burtForecaster
Electric Utility Load Forecaster Application

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![run_pytest](https://github.com/dpinney/burtForecaster/actions/workflows/run_pytest.yaml/badge.svg)](https://github.com/dpinney/burtForecaster/actions/workflows/run_pytest.yaml)

## Installation

Create a python 3.9 virtual environment and download packages from `requirements.txt`:

```sh
python3.9 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the application

After installation, run the application by executing the run script:

```sh
source run.sh
```

Or you can use docker:

```
docker image build -t burt_forecaster .
docker run -p 1546:1546 forecaster_app
```

And view the application at http://localhost:1546/

## Development

### Install black pre-commit

In order to follow black style guidelines, simply run the following command:

```sh
pre-commit install
```

This will prevent you from committing un-styled code.