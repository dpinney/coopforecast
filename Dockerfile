FROM amd64/python:3.8-buster
WORKDIR /code
COPY . .
RUN pip install --upgrade pip
RUN pip install -r requirements.lock

CMD ["python", "deploy.py"]