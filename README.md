# burtForecaster
Electric Utility Load Forecaster Application

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![run_pytest](https://github.com/dpinney/burtForecaster/actions/workflows/run_pytest.yaml/badge.svg)](https://github.com/dpinney/burtForecaster/actions/workflows/run_pytest.yaml)

## Launch with docker

```sh
docker image build -t burt_forecaster .
docker run -p 5000:5000 forecaster_app -v "`pwd`/forecast_app":/forecast_app forecaster_app
```

And view the application at http://localhost:5000/. The `-v` flag allows you to 
sync your local files to the docker container for code editing.

## Launch without docker

Create a python 3.9 virtual environment and download packages from `requirements.txt`:

```sh
python3.9 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

After installation, run the application by executing the run script:

```sh
source run.sh
```

## Development

### Install black pre-commit

In order to follow black style guidelines, simply run the following command:

```sh
pre-commit install
```

This will prevent you from committing un-styled code.