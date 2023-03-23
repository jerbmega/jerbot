# syntax=docker/dockerfile:1

FROM python:3.10-slim-bullseye

WORKDIR /jerbot

COPY requirements.txt requirements.txt
RUN apt-get update && apt-get install build-essential -y
RUN pip3 install -r requirements.txt

COPY main.py .
COPY err.py .
copy db.py .
COPY scheduler.py .

COPY plugins plugins

CMD ["python3", "-O", "main.py"]
