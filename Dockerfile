FROM --platform=linux/amd64 ubuntu:20.04
WORKDIR /code
ENV PYTHONUNBUFFERED 1

# Install base utilities
RUN apt-get update
RUN apt-get install -y python3.8
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y sudo systemd letsencrypt python3-pip authbind

RUN pip install tensorflow==2.7.0

COPY requirements.lock requirements.lock
RUN pip install -r requirements.lock

# Copy contents of systemd and launch install.sh
#  but because we're in a container, we can't use the host's systemd
