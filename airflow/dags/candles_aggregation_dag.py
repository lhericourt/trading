import logging

from airflow import DAG
from operators.candles_aggregation import CandleAggregation

from datetime import datetime, timedelta
logger = logging.getLogger(__name__)

default_args = {
    'start_date': datetime(2020, 12, 23),
    'owner': 'airflow',
    'retries': 3,
    'retry_delay': timedelta(minutes=1),
    'max_active_runs': 1,
    'catchup': True
}

with DAG(dag_id='trading_candles_aggregation', schedule_interval="@monthly", default_args=default_args) as dag:
    aggregated_candles = CandleAggregation(task_id='candles_aggregation',  provide_context=True, scope='month')

