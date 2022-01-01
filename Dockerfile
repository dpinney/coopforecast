FROM --platform=linux/amd64 ubuntu:20.04
WORKDIR /code
ENV PYTHONUNBUFFERED 1

# Install base utilities
RUN apt-get update
RUN apt-get install -y python3.8
RUN apt install -y python3-pip

RUN pip install tensorflow==2.7.0

COPY requirements.lock requirements.lock
RUN pip install -r requirements.lock
