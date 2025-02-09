from include.helpers.minio import get_minio_client
from airflow.hooks.base import BaseHook
from io import BytesIO
import requests
import json
import logging
import itertools
import pandas as pd
from numpy.linalg import LinAlgError
from statsmodels.tsa.arima.model import ARIMA
import os
import pendulum

import mlflow

def _get_stock_prices(url, symbol):
    # Download stock prices from the yfinance website.
    url = f"{url}{symbol}?metrics=high?&interval=60m&range=1y"
    api = BaseHook.get_connection('stock_api')
    response = requests.get(url, headers=api.extra_dejson['headers'])
    return json.dumps(response.json()['chart']['result'][0])

def _store_prices(prices):
    # Format and store prices on s3
    prices = json.loads(prices)
    client = get_minio_client()
    bucket_name = 'stock-market'
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
    symbol = prices['meta']['symbol']
    data = json.dumps(prices, ensure_ascii=False).encode('utf8')
    objw = client.put_object(
        bucket_name=bucket_name,
        object_name=f'{symbol}/prices.json',
        data=BytesIO(data),
        length=len(data)
        )
    return f'{objw.bucket_name}/{symbol}'
    
def _get_formatted_prices_url(location):
    # Get url of an object from s3.
    client = get_minio_client()
    objects = client.list_objects(f'stock-market', prefix='AAPL/formatted_prices/', \
                                  recursive=True)
    csv_file = [obj for obj in objects if obj.object_name.endswith('.csv')][0]
    return f's3://{csv_file.bucket_name}/{csv_file.object_name}'

def _get_formatted_prices_object(location, code="AAPL"):
    # Get data object from s3.
    try:
        storage_options = {
            'key': 'minio',
            'secret': "minio123",
            'endpoint_url': "http://minio:9000",
        }
        historical_data = pd.read_csv(f's3://stock-market/AAPL/formatted_prices/part-00000-6a56291e-c8cd-429f-b1d9-0ea1eccdce4e-c000.csv', \
                                      storage_options=storage_options)
        print(historical_data.tail(10))
        return historical_data
    except Exception as e:
        logging.error(e)

def _train_arima(url, trend="c", **kwargs) -> str:
    """Train ARIMA Model and log on MLFlow Server."""
    storage_options = {
        'key': 'minio',
        'secret': "minio123",
        'endpoint_url': "http://minio:9000",
    }

    df = pd.read_csv(url, storage_options=storage_options)
    # Convert the timestamp to datetime as follows. 's' for seconds, 'ms' for milliseconds
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')

    # Create timeseries
    df.set_index('timestamp', inplace=True)
    print(df.index[:10])
    df = df.dropna()
    df.sort_index(ascending=True, inplace=True)

    # Find the best model
    p = q = range(0, 9)
    d = range(0, 3)
    # Generate all the combinations for p d q
    pdq = list(itertools.product(p, d, q))
    arima_model = []
    arima_results = []
    for param_set in pdq:
        try:
            arima = ARIMA(df.close, order=param_set, trend=trend)
            arima_fitted = arima.fit()
            arima_model.append(arima_fitted)
            arima_results.append(arima_fitted.aic)
        except:
            continue
    logging.info('**' * 25)
    print('The lowest AIC score is {:.4f} and parameters are {}'
          .format(pd.DataFrame(arima_results)
                  .where(pd.DataFrame(arima_results).T.notnull() \
                         .all()).min()[0],
                  pdq[arima_results.index(min(arima_results))]))
    p, d, q = pdq[arima_results.index(min(arima_results))]

    # Best model is the model with the lowest AIC score
    best_model = arima_model[arima_results.index(min(arima_results))]

    mlflow.set_tracking_uri('http://tracker_mlflow:5000')
    exp_name = f"STOCK_PRICES_ARIMA({p},{d},{q})_{trend}"
    mlflow.set_experiment(exp_name)

    convergence_error, stationarity_error = 0, 0
    with mlflow.start_run() as run:
        mlflow.set_tag("run_id", "run_id")

        mlflow.log_params(
            dict(p=p, d=d, q=q, trend=trend, trained_time=str(pendulum.DateTime.now()))
        )

        try:
            model_summary = best_model.summary().as_text()
            with open(f"model_summary_{exp_name}.txt", "w") as f:
                f.write(model_summary)
            y_pred = best_model.forecast(steps=1).values[0]
            aic = best_model.aic
            bic = best_model.bic
            results = dict(
                y_pred=y_pred,
                aic=aic,
                bic=bic,
                convergence_error=convergence_error,
                stationarity_error=stationarity_error,
            )
            results.update(best_model.pvalues)
            mlflow.log_metrics(results)
            logged_result = mlflow.statsmodels.log_model(
                best_model, artifact_path=exp_name, registered_model_name=exp_name
            )
            mlflow.log_artifact(f"model_summary_{exp_name}.txt")
            os.remove(f"model_summary_{exp_name}.txt")
            logger = logging.getLogger(__name__)
            logger.info(logged_result)
            # can also use the following best_model.model_uri
            return f'runs:/{run.info.run_id}/{exp_name}'

        # LinAlgError is used to log and handle cases where the ARIMA model's
        # training fails due to convergence issues or numerical instability
        # during matrix operations (e.g., during model fitting or optimization).
        except LinAlgError:
            results = dict(convergence_error=1, stationarity_error=0)
            mlflow.log_metrics(results)
            return ""
        except ValueError:
            results = dict(convergence_error=0, stationarity_error=1)
            mlflow.log_metrics(results)
            return ""

def _predict_price(logged_model: str, url: str, **kwargs) -> str:
    """Predict prices"""
    # Load model as a PyFuncModel.
    loaded_model = mlflow.statsmodels.load_model(logged_model)

    storage_options = {
        'key': 'minio',
        'secret': "minio123",
        'endpoint_url': "http://minio:9000",
    }

    df = pd.read_csv(url, storage_options=storage_options)

    predictions = loaded_model.predict(start=0 ,end=len(df))
    return json.dumps(predictions.tolist())
