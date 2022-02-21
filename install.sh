#!/bin/bash

export REPO="/opt/coopforecast"

export EMAIL=$(python3 -c "from forecast_app.config import EMAIL; print(EMAIL)")
export DOMAIN=$(python3 -c "from forecast_app.config import DOMAIN; print(DOMAIN)")

# If crontab hasn't been set up, set it up
if [ $(crontab -l | grep -v "^#" | wc -l) -eq 0 ]; then
    export ADMIN_USER=$(python3 -c "from forecast_app.secret_config import ADMIN_USER; print(ADMIN_USER)")
    export ADMIN_PASSWORD=$(python3 -c "from forecast_app.secret_config import ADMIN_PASSWORD; print(ADMIN_PASSWORD)")
    export LOGIN_CONFIG="--username $ADMIN_USER --password='$ADMIN_PASSWORD' --url https://coopforecast.com"

    # Pull from the weather APIs every hour
    export WEATHER_SYNC_CRON="0 * * * * /usr/bin/python3 $REPO/cli.py sync-weather-data $LOGIN_CONFIG"
    (crontab -l ; echo "$WEATHER_SYNC_CRON")| crontab -
    
    # Every day at 7:05 am, launch a new model
    export FORECAST_INIT_CRON="05 07 * * * /usr/bin/python3 $REPO/cli.py launch-new-model $LOGIN_CONFIG"
    (crontab -l ; echo "$FORECAST_INIT_CRON")| crontab -
fi

DEBIAN_FRONTEND=noninteractive sudo apt-get install -y systemd letsencrypt python3-pip authbind
pip3 install tensorflow==2.7.0
pip3 install -r $REPO/requirements.txt
export PATH=/home/ubuntu/.local/bin:$PATH

sudo ln -s $REPO/systemd/coopforecast.service /etc/systemd/system/coopforecast.service
sudo ln -s $REPO/systemd/cert.service /etc/systemd/system/cert.service
sudo ln -s $REPO/systemd/cert.timer /etc/systemd/system/cert.timer

# Setup TLS
sudo certbot certonly --standalone --agree-tos -n -m $EMAIL -d $DOMAIN

# Add ubuntu user:group
sudo useradd -r ubuntu
sudo chown -R ubuntu:ubuntu ./
sudo chown -R ubuntu:ubuntu /etc/letsencrypt
sudo chown -R ubuntu:ubuntu /var/log/letsencrypt

# configure authbind so r3it can bind to low-numbered ports sans root.
sudo touch /etc/authbind/byport/80
sudo touch /etc/authbind/byport/443
sudo chown ubuntu:ubuntu /etc/authbind/byport/80
sudo chown ubuntu:ubuntu /etc/authbind/byport/443
sudo chmod 710 /etc/authbind/byport/80
sudo chmod 710 /etc/authbind/byport/443

# create directory for LetsEncrypt acme challenges.
sudo mkdir -p $REPO/.well-known/acme-challenge

# Ensure timezone is correct
sudo ln -sf /usr/share/zoneinfo/America/Chicago /etc/localtime

# enable
sudo systemctl enable /etc/systemd/system/coopforecast.service
sudo systemctl start coopforecast
sudo systemctl enable /etc/systemd/system/cert.service
sudo systemctl enable /etc/systemd/system/cert.timer
