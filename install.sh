#!/bin/bash
# TODO: Migrate to cli.py?

export REPO="/opt/burtForecaster"
export EMAIL=$(python -c "from forecast_app.secret_config import EMAIL")
export DOMAIN=$(python -c "from forecast_app.secret_config import DOMAIN")

DEBIAN_FRONTEND=noninteractive apt-get install -y sudo systemd letsencrypt python3-pip authbind
pip3 install tensorflow==2.7.0
pip3 install -r $REPO/requirements.lock
export PATH=/home/ubuntu/.local/bin:$PATH

sudo ln -s $REPO/systemd/burt_forecaster.service /etc/systemd/system/burt_forecaster.service
sudo ln -s $REPO/systemd/cert.service /etc/systemd/system/cert.service
sudo ln -s $REPO/systemd/cert.timer /etc/systemd/system/cert.timer

# Setup TLS
sudo certbot certonly --standalone --agree-tos -n -m $EMAIL -d $DOMAIN

# Add ubuntu user:group
sudo useradd -r ubuntu
sudo chown -R ubuntu:ubuntu ./
sudo chown -R ubuntu:ubuntu /etc/letsencrypt

# configure authbind so r3it can bind to low-numbered ports sans root.
sudo touch /etc/authbind/byport/80
sudo touch /etc/authbind/byport/443
sudo chown ubuntu:ubuntu /etc/authbind/byport/80
sudo chown ubuntu:ubuntu /etc/authbind/byport/443
sudo chmod 710 /etc/authbind/byport/80
sudo chmod 710 /etc/authbind/byport/443

# create directory for LetsEncrypt acme challenges.
sudo mkdir -p $REPO/.well-known/acme-challenge

# enable
sudo systemctl enable /etc/systemd/system/burt_forecaster.service
sudo systemctl start burt_forecaster
sudo systemctl enable /etc/systemd/system/cert.service
sudo systemctl enable /etc/systemd/system/cert.timer
