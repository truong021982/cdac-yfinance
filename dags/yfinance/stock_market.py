from airflow.decorators import dag, task
import pendulum
from airflow.models.baseoperator import chain
from airflow.hooks.base import BaseHook
from airflow.sensors.base import PokeReturnValue
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.providers.slack.notifications.slack import SlackNotifier
from airflow.operators.python import PythonOperator
from include.stock_market.tasks import _get_stock_prices, \
    _store_prices, \
    _get_formatted_prices_url, \
    _train_arima, \
    _predict_price
import requests

# ======================= Set Configs =======================
SCHEDULE_INTERVAL = "0 5 * * *"
# Indian tz
UCT = pendulum.timezone("Asia/Kolkata")
start_date = pendulum.yesterday(tz=UCT)
# ==========================================================

SYMBOL='AAPL'

@dag(
    start_date=start_date,
    schedule='@daily',
    catchup=False,
    tags=['stock_market'],
    on_success_callback=SlackNotifier(
        text="{{ dag.dag_id }} DAG succeeded!", 
        channel="#monitoring", 
        slack_conn_id="slack"),
)
def stock_market():

    @task.sensor(poke_interval=30, timeout=3600, mode='poke')
    def is_api_available() -> PokeReturnValue:
        api = BaseHook.get_connection('stock_api')
        url = f"{api.host}{api.extra_dejson['endpoint']}"
        response = requests.get(url, headers=api.extra_dejson['headers'])
        condition = response.json()['finance']['result'] is None # <-- changed
        return PokeReturnValue(is_done=condition, xcom_value=url)

    get_stock_prices = PythonOperator(
        task_id='get_stock_prices',
        python_callable=_get_stock_prices,
        op_kwargs={'url': '{{ ti.xcom_pull(task_ids="is_api_available") }}', 'symbol': SYMBOL},
    )

    store_prices = PythonOperator(
        task_id='store_prices',
        python_callable=_store_prices,
        op_kwargs={'prices': '{{ ti.xcom_pull(task_ids="get_stock_prices") }}'},
    )

    format_prices = DockerOperator(
        task_id='format_prices',
        max_active_tis_per_dag=1,
        image='airflow/spark-app',
        container_name='trigger_job',
        environment={
            'SPARK_APPLICATION_ARGS': '{{ ti.xcom_pull(task_ids="store_prices")}}'
        },
        api_version='auto',
        auto_remove=True,
        docker_url='tcp://host.docker.internal:2375',
        network_mode='container:spark-master',
        tty=True,
        xcom_all=False,
        mount_tmp_dir=False
    )

    get_formatted_csv = PythonOperator(
        task_id='get_formatted_csv',
        python_callable=_get_formatted_prices_url,
        op_kwargs={'location': '{{ ti.xcom_pull(task_ids="store_prices") }}'},
    )

    # Train the model and log training metrics.
    train_arima = PythonOperator(
        task_id='train_arima',
        python_callable=_train_arima,
        op_kwargs={'url': '{{ ti.xcom_pull(task_ids="get_formatted_csv") }}'},
    )

    predict_price = PythonOperator(
        task_id='predict_price',
        python_callable=_predict_price,
        op_kwargs={'logged_model': '{{ ti.xcom_pull(task_ids="train_arima") }}',
                   'url': '{{ ti.xcom_pull(task_ids="get_formatted_csv") }}'},
    )

    chain(
        is_api_available(),
        get_stock_prices,
        store_prices,
        format_prices,
        get_formatted_csv,
        train_arima,
        predict_price
        )

stock_market()