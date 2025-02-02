# CDAC Yahoo Finance Project

This is my final project code-base for [CDAC]()'s PG-DBDA course using Airflow, MinIO, Spark and MLFlow. 

## Time Series Forecasting Introduction

<img src = "./ml-timeseries.png" width="90%">

## Prerequisites
- Install docker
  - Create .env like below for docker compose under the root
  ```
  # MinIO
  AWS_ACCESS_KEY_ID=minio
  AWS_SECRET_ACCESS_KEY=minio123
  AWS_REGION=us-east-1

  # MLFLOW config
  MLFLOW_S3_ENDPOINT_URL=http://minio:9000
  MLFLOW_TRACKING_URI=http://mlflow:5000
  AWS_BUCKET_NAME=mlflow

  # MySQL config
  MYSQL_DATABASE=mlflow
  MYSQL_USER=mlflow_user
  MYSQL_PASSWORD=mlflow_password
  MYSQL_ROOT_PASSWORD=toor
  ```
## Spark Requirements
- SPARK_APPLICATION_ARGS will be passed to the Spark application as an argument -e when running the Spark application from Airflow
- You need to allocate at least 8gb of RAM to Docker Desktop. To do this, go to Docker Desktop -> Preferences -> Resources -> Advanced -> Memory

## How to run
- start all docker containers
    ```bash
    $ astro dev start
    ```

- stop all the docker containers
    ```bash
    $ astro dev stop
    ```

- force stop and remove all the docker containers
    ```bash
    $ astro dev kill
    ```

- To train ARIMA and auto-ARIMA run `stock_market` DAG

## Endpoints
- Airflow:
    - http://localhost:8080/
- MLflow
    - http://localhost:5000/
- MinIO
    - http://localhost:9000/

## References
- Dockerized MLFlow Server
    - https://github.com/Toumash/mlflow-docker
    - https://www.mlflow.org/docs/latest/tracking.html#scenario-4-mlflow-with-remote-tracking-server-backend-and-artifact-stores