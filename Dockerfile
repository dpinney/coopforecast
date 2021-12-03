FROM python:3.9-bullseye
WORKDIR /code
COPY . .
RUN pip install -r requirements.txt

CMD ["python", "deploy.py"]