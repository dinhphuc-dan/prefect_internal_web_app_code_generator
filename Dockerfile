# FROM prefecthq/prefect:2.13.5-python3.10
FROM python:3.10.0-alpine3.15 

# upgrade pip to the latest version and config timezone
RUN apk --no-cache upgrade \
    && pip install --upgrade pip \
    && apk --no-cache add tzdata

ENV TZ=Asia/Ho_Chi_Minh

# install git and bash
RUN apk update \
    && apk --no-cache add git \
    && apk --no-cache add bash

WORKDIR /app

# copy project file to image
COPY . /app

RUN pip install -r requirements.txt --trusted-host pypi.python.org --no-cache-dir

