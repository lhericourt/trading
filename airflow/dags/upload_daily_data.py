import logging

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from operators.any_to_db import AnyToDb

from datetime import datetime, timedelta
from data.candle import get_candles_all_symbols
from data.economic_calendar import get_events_on_period

logger = logging.getLogger(__name__)

default_args = {
    'start_date': datetime(2020, 12, 1),
    'owner': 'airflow',
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'max_active_runs': 1,
    'catchup': True
}

with DAG(dag_id='trading_daily_import', schedule_interval="@daily", default_args=default_args) as dag:
    uploading_events = AnyToDb(task_id="uploading_events", provide_context=True, table_name='event',
                               function=get_events_on_period, first_delete=True)
    uploading_candles = AnyToDb(task_id="uploading_candles", provide_context=True, table_name='candle',
                                function=get_candles_all_symbols)
    uploading_events >> uploading_candles

