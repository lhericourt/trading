import os
from typing import Tuple, List, Optional
from pathlib import Path
from datetime import datetime, timedelta
import re
from enum import Enum

import psycopg2
import pandas as pd
import numpy as np
from pandas.io.sql import read_sql
from sklearn.linear_model import LinearRegression


class AnnualGranularity(Enum):
    MIN_5 = 252 * 24 * 12
    MIN_15 = 252 * 24 * 4
    MIN_30 = 252 * 24 * 2
    H_1 = 252 * 24
    H_4 = 252 * 6
    D_1 = 252


def get_password(env_variable: str) -> str:
    password_path = os.environ[env_variable]
    if Path(password_path).is_file():
        password = Path(password_path).read_text()
    else:
        password = Path(os.environ['TRADING_HOME'], password_path).read_text()
    return password


def get_nb_days(start: str, end: str) -> int:
    s_date = datetime.strptime(start, '%Y-%m-%d')
    e_date = datetime.strptime(end, '%Y-%m-%d')
    return (e_date - s_date).days


def add_days_to_date(date: str, nb_days: int) -> str:
    date = datetime.strptime(date, '%Y-%m-%d')
    new_date = date + timedelta(days=nb_days)
    return new_date.strftime('%Y-%m-%d')


def split_period_by_chunk(start: str, end: str, chunk_size: int) -> List[Tuple[str, str]]:
    split_dates = list()
    nb_days = get_nb_days(start, end)
    nb_iter = (nb_days // chunk_size) + 1 if nb_days % chunk_size != 0 else nb_days // chunk_size

    for i in range(nb_iter):
        start_idx = i * chunk_size
        end_idx = min((i + 1) * chunk_size, nb_days)
        start_date = add_days_to_date(start, start_idx)
        end_date = add_days_to_date(start, end_idx)
        split_dates.append((start_date, end_date))
    return split_dates


def convert_to_number(val: str) -> Optional[float]:
    if val is None:
        return None
    number_patter = r'([a_zA-Z%])'
    processed_val = re.sub(number_patter, '', val).replace('.', '').replace(',', '.')
    try:
        processed_val = float(processed_val)
    except Exception:
        processed_val = None
    return processed_val


def compute_average(data: pd.Series, span: int = 14,  avg_type: str = 'ma') -> pd.Series:
    """
    :param data: series of data to compute the mean
    :param span: the historical of date to take into account to compute the mean
    :param avg_type:
    - value 'ma' for a moving average
    - value 'ewm' for an exponential moving average
    - value 'wws' for Welles Wilder smoothing average
    :return: a new seris with the values of the selected average type
    """
    if avg_type == 'ma':
        avg = data.rolling(span).mean()
    elif avg_type == 'ewm':
        avg = data.ewm(span=span, min_periods=span).mean()
    elif avg_type == 'wws':
        avg = data.ewm(alpha=1/span, min_periods=span, adjust=False).mean()
    else:
        avg = pd.Series([np.NaN] * len(data))

    return avg


def get_candles(dsn, schema, start_date, end_date):
    candles = pd.DataFrame()
    with psycopg2.connect(dsn) as conn:
        for table in ['candle', 'candle15m', 'candle30m', 'candle1h', 'candle4h', 'candle1d']:
            sql = f'set search_path = {schema};'
            sql += f'''
                SELECT '{table}' as table, date, symbol, open, close, low, high, tickqty
                FROM {table}
                WHERE date >= %(start_date)s and date < %(end_date)s 
                order by symbol, date
            '''
            candles_tmp = read_sql(sql, conn, params={'start_date': start_date, 'end_date': end_date})
            candles = pd.concat([candles, candles_tmp])
    candles.reset_index(drop=True, inplace=True)
    return candles


def compute_sign_changement(data, col, span):
    data['sign'] = np.where(data[col] < 0, -1, 1)
    sign_sum = data['sign'].rolling(span).sum()
    change_sign = np.where(np.abs(sign_sum) != span, 1, 0)
    change_sign_pos = np.where((change_sign == 1) & (data[col] > 0), 1, 0)
    change_sign_neg = np.where((change_sign == 1) & (data[col] < 0), 1, 0)
    del data['sign']
    return change_sign_pos, change_sign_neg


def compute_slope(candles, idx, span=5, before=True):
    if before:
        y = candles.loc[idx - span + 1:idx, ['close']]
    else:
        y = candles.loc[idx: idx + span - 1, ['close']]
    x = np.arange(span).reshape((span, 1))
    y_scaled = (y - y.min()) / (y.max() - y.min())
    if len(y_scaled[y_scaled.isnull().any(axis=1)]):
        return 0
    x_scaled = (x - x.min()) / (x.max() - x.min())
    lr = LinearRegression()
    try:
        lr.fit(x_scaled, y_scaled)
    except:
        return 0
    return np.rad2deg(np.arctan(lr.coef_[0]))[0]