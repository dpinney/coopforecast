# coopforecast
Electric Utility Load Forecaster Application

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![run_pytest](https://github.com/dpinney/coopforecast/actions/workflows/run_pytest.yaml/badge.svg)](https://github.com/dpinney/coopforecast/actions/workflows/run_pytest.yaml)
[![codecov](https://codecov.io/gh/dpinney/coopforecast/branch/main/graph/badge.svg?token=MUTWHY0DJE)](https://codecov.io/gh/dpinney/coopforecast)

## Application Deployment

* Bring up an [Ubuntu 20.04 LTS](https://releases.ubuntu.com/20.04/) machine.
* Configure DNS to point to new VM (needed for TLS cert creation).
* Ensure ports 443 and 80 are open (e.g., on hosting provider's firewall).
* Clone the repo: `git clone https://github.com/dpinney/coopforecast` to `/opt/`
* Ensure `config.py` (especially the `prod` config) reflects the client's needs.
* Configure the app's secrets. You can copy the sample file `cp forecast_app/secret_config.py.sample forecast_app/secret_config.py`.
* Run the install script `install.sh`. This will set up TLS certs, cron commands, and timezone.
  * It may be easier to first install the major apt packages and then run the install script: `sudo apt-get install -y systemd letsencrypt python3-pip authbind`
  * You may need to add the python packages to the PATH: `export PATH=/home/ubuntu/.local/bin:$PATH`
* Double check that the crontab is properly configured with `crontab -e`.
* Double check that all tests pass with `pytest`.
* Setup the new database with the CLI: `python3 cli.py restart-db --config=prod`

The install script is idempotent, so when updating the application, simply 
run the `install.sh` again. Depending on the change, you may also have to 
run `sudo systemctl restart coopforecast`.

## Local Development
### Launch without docker (recommended)

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


### Launch with docker

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

### Prepare database

To initialize the database and fill with demo data run the following commands:

```sh
# Remove existing database and create a new one
python cli.py restart-db --config dev
# Load demo data into database
python cli.py demo --config dev
```

### Launch tensorboard

[Tensorboard](https://www.tensorflow.org/tensorboard) logs are placed in the `tb-logs` directory (ignored in version control).
To view detailed visualizations of the model's training and structure, launch tensorboard from the command line:

```sh
tensorboard --logdir=tb-logs
```

### Generate documentation

[`pdoc`](https://pdoc.dev/) library is used to generate documentation. To rebuild documentation, run

```sh
pdoc -o docs forecast_app
```

and commit updates to publish to the static site.

### Install pre-commit

In order to follow `black` and `isort` style guidelines, simply run the following command:

```sh
pre-commit install
```

This will prevent you from committing un-styled code.