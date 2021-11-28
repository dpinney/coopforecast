# burtForecaster
Electric Utility Load Forecaster Application

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
