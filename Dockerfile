# FROM prefecthq/prefect:2.13.5-python3.10
FROM python:3.10.0-slim 

# upgrade pip to the latest version and config timezone
RUN apt-get update \
    && pip install --upgrade pip \
    && apt-get install tzdata -y

ENV TZ=Asia/Ho_Chi_Minh

# install git and bash
RUN apt-get update \
    && apt-get install git -y \
    && apt-get install bash -y 

WORKDIR /app

# copy project file to image
COPY . /app

RUN pip install -r requirements.txt --trusted-host pypi.python.org --no-cache-dir

