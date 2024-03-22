FROM prefecthq/prefect:2.13.5-python3.10
WORKDIR /app
COPY ./requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt --trusted-host pypi.python.org --no-cache-dir
COPY ./entrypoint.sh /app/entrypoint.sh