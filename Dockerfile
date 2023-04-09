FROM python:3.10

ENV TZ="Europe/Warsaw"

WORKDIR /app

COPY requirements.txt /app

RUN pip3 install -r requirements.txt

COPY . /app