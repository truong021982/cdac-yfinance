# CDAC Yahoo Finance Project

This repository is my final project for [CDAC]()'s PG-DBDA course using Airflow, MinIO, Spark and MLFlow. 

## Time Series Forecasting

<img src = "./ml-timeseries.png" width="100%">

## Architecture

<img src = "./imgs/architecture.png" width="100%">


## Prerequisites
- Install docker. If you use docker on window, please do the following configuration for Docker Desktop:

<img src = "./imgs/docker_desktop_1.png" width="100%">
<img src = "./imgs/docker_desktop_2.png" width="100%">
<img src = "./imgs/docker_desktop_3.png" width="100%">
  
- Install astro cli from Astronomer website
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
- You need to allocate at least 8gb of RAM to Docker Desktop. To do this, go to Docker Desktop -> Preferences -> Resources -> Advanced -> Memory

## How to run
- Build the spark application
    ```bash
    $ docker build ./spark/notebooks/stock_transform -t airflow/spark-app
    $ docker build ./spark/master -t airflow/spark-master
    $ docker build ./spark/worker -t airflow/spark-worker
    ```
- initialize the project
    ```bash
    $ astro dev init
    ```
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

- To train ARIMA run `stock_market` DAG

## How to use Dashboards 
### Airflow Dashboard: 

Login creds is admin:admin

    - http://localhost:8080/

<img src = "./imgs/air_flow_1.png" width="100%">
<img src = "./imgs/air_flow_2.png" width="100%">
<img src = "./imgs/air_flow_3.png" width="100%">
<img src = "./imgs/air_flow_4.png" width="100%">
<img src = "./imgs/air_flow_5.png" width="100%">
<img src = "./imgs/air_flow_6.png" width="100%">

### MLflow Dashboard:
    - http://localhost:5000/

<img src = "./imgs/mlflow_1.png" width="100%">
<img src = "./imgs/mlflow_2.png" width="100%">
<img src = "./imgs/mlflow_3.png" width="100%">
<img src = "./imgs/mlflow_4.png" width="100%">
<img src = "./imgs/mlflow_5.png" width="100%">

### MinIO Dashboard:
    - http://localhost:9000/

<img src = "./imgs/minio_1.png" width="100%">
<img src = "./imgs/minio_2.png" width="100%">
<img src = "./imgs/minio_3.png" width="100%">
<img src = "./imgs/minio_4.png" width="100%">
<img src = "./imgs/minio_5.png" width="100%">

## References
- Dockerized MLFlow Server
    - https://github.com/Toumash/mlflow-docker
    - https://www.mlflow.org/docs/latest/tracking.html#scenario-4-mlflow-with-remote-tracking-server-backend-and-artifact-stores