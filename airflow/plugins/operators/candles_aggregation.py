from datetime import datetime

from airflow.models.baseoperator import BaseOperator
from airflow.hooks.postgres_hook import PostgresHook
from airflow.utils.decorators import apply_defaults
import pandas as pd
from pandas.io.sql import read_sql

from db.utils import insert_df_to_db, delete_data
from utils.utils import add_days_to_date

AGG = {'open': 'first',
       'close': 'last',
       'low': 'min',
       'high': 'max'
       }

COLS = ['symbol', 'day', 'open', 'close', 'low', 'high']


def compute_one_day_agg(candles: pd.DataFrame) -> (str, pd.DataFrame):
    candles_day = candles[COLS].groupby(['symbol', 'day']).aggregate(AGG).reset_index()
    candles_day.rename(columns={'day': 'date'}, inplace=True)
    candles_day['date'] = candles_day['date'].astype(str) + ' 00:00:00'
    return 'candle1d', candles_day


def compute_four_hours_agg(candles: pd.DataFrame) -> (str, pd.DataFrame):
    candles_4hours = candles[COLS + ['hour4']].groupby(['symbol', 'day', 'hour4']).aggregate(AGG).reset_index()
    candles_4hours.rename(columns={'day': 'date'}, inplace=True)
    candles_4hours['date'] = candles_4hours['date'].astype(str) + ' ' + candles_4hours['hour4'] + ':00:00'
    del candles_4hours['hour4']
    return 'candle4h', candles_4hours


def compute_one_hour_agg(candles: pd.DataFrame) -> (str, pd.DataFrame):
    candles_hour = candles[COLS + ['hour']].groupby(['symbol', 'day', 'hour']).aggregate(AGG).reset_index()
    candles_hour.rename(columns={'day': 'date'}, inplace=True)
    candles_hour['date'] = candles_hour['date'].astype(str) + ' ' + candles_hour['hour'] + ':00:00'
    del candles_hour['hour']
    return 'candle1h', candles_hour


def compute_30min_agg(candles: pd.DataFrame) -> (str, pd.DataFrame):
    candles_30min = candles[COLS + ['hour', 'min30']].groupby(['symbol', 'day', 'hour', 'min30']
                                                              ).aggregate(AGG).reset_index()
    candles_30min.rename(columns={'day': 'date'}, inplace=True)
    candles_30min['date'] = candles_30min['date'].astype(str) + ' ' + candles_30min['hour'] + ':' +\
                            candles_30min['min30'] + ':00'
    del candles_30min['hour']
    del candles_30min['min30']
    return 'candle30m', candles_30min


def compute_15min_agg(candles: pd.DataFrame) -> (str, pd.DataFrame):
    candles_15min = candles[COLS + ['hour', 'min15']].groupby(['symbol', 'day', 'hour', 'min15']
                                                              ).aggregate(AGG).reset_index()
    candles_15min.rename(columns={'day': 'date'}, inplace=True)
    candles_15min['date'] = candles_15min['date'].astype(str) + ' ' + candles_15min['hour'] + ':' +\
                            candles_15min['min15'] + ':00'
    del candles_15min['hour']
    del candles_15min['min15']
    return 'candle15m', candles_15min


class CandleAggregation(BaseOperator):
    @apply_defaults
    def __init__(self, scope, *args, **kwargs) -> None:
        self.scope = scope
        super().__init__(*args, **kwargs)

    @staticmethod
    def _one_digit_to_two_digits(x: float) -> str:
        return str(int(x)) if len(str(int(x))) > 1 else '0' + str(int(x))

    @staticmethod
    def _monthly_date(date: datetime) -> (str, str):
        date = date.strftime("%Y-%m-%d")
        year, month = date.split('-')[: -1]
        start_date = year + '-' + month + '-01'

        next_month = int(month) + 1 if int(month) < 12 else 1
        next_month = str(next_month) if len(str(next_month)) > 1 else '0' + str(next_month)
        year = year if next_month == '01' else str(int(year) + 1)
        end_date = year + '-' + next_month + '-01'
        return start_date, end_date

    def execute(self, context):
        schema = 'trading'

        if self.scope == 'month':
            start_date, end_date = CandleAggregation._monthly_date(context['execution_date'])

        elif self.scope == 'day':
            start_date = context['execution_date'].strftime("%Y-%m-%d")
            end_date = add_days_to_date(start_date, 1)

        params = {'start_date': start_date,
                  'end_date': end_date}

        pg_hook = PostgresHook(postgres_conn_id='trading', schema=schema)
        with pg_hook.get_conn() as conn:
            request = f'SET SEARCH_PATH TO {schema};'
            request += '''SELECT symbol, date, (date)::date AS day, 4 * (EXTRACT(HOUR FROM date)::INT / 4) AS hour4,
                            EXTRACT(HOUR FROM date) AS hour,
                            30 * (EXTRACT(MINUTE FROM date)::INT / 30) AS min30,
                            15 * (EXTRACT(MINUTE FROM date)::INT / 15) AS min15,
                            open, close, low, high
                          FROM candle
                          WHERE date >= %(start_date)s AND date < %(end_date)s
                          ORDER BY symbol, date;'''
            candles = read_sql(request, conn, params=params)
            candles['hour'] = candles.apply(axis=1, func=lambda x: CandleAggregation._one_digit_to_two_digits(x['hour']))
            candles['hour4'] = candles.apply(axis=1, func=lambda x: CandleAggregation._one_digit_to_two_digits(x['hour4']))
            candles['min30'] = candles.apply(axis=1, func=lambda x: CandleAggregation._one_digit_to_two_digits(x['min30']))
            candles['min15'] = candles.apply(axis=1, func=lambda x: CandleAggregation._one_digit_to_two_digits(x['min15']))

        for agg_func in [compute_one_day_agg, compute_four_hours_agg, compute_one_hour_agg, compute_30min_agg,
                         compute_15min_agg]:
            table_name, agg_candles = agg_func(candles)
            insert_df_to_db(conn, agg_candles, table_name, schema)

        return


