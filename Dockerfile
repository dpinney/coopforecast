FROM amd64/python:3.8-buster
WORKDIR /code
ENV PYTHONUNBUFFERED 1
RUN pip install --upgrade pip
COPY requirements.lock requirements.lock
RUN pip install -r requirements.lock