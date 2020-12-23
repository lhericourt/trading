import os
import logging
from traceback import print_tb

from fxcmpy import fxcmpy
import pandas as pd

from db.utils import insert_df_to_db, get_uri_db
from utils.utils import get_password, split_period_by_chunk, add_days_to_date

logger = logging.getLogger(__name__)

SYMBOLS = ['EUR/USD', 'USD/JPY', 'GBP/USD', 'AUD/USD', 'USD/CAD', 'USD/CHF', 'USD/HKD', 'EUR/GBP']


class FCXMContextManager(object):
    def __init__(self, access_token: str, log_level: str, server: str, log_file: str) -> None:
        self.conn = fxcmpy(access_token=access_token, log_level=log_level, server=server, log_file=log_file)

    def __enter__(self) -> fxcmpy:
        return self.conn

    def __exit__(self, type_, value, traceback):
        self.conn.close()
        if type_ is not None:
            logger.error(f'{type_} : {value}')
            print_tb(traceback)
        return True


def get_candles(symbol: str, period: str = 'm5', start: str = None, end: str = None) -> pd.DataFrame:
    logger.info(f"Getting candles from FXCM for symbol {symbol} from {start} to {end}")
    access_token = get_password('TRADING_FXCM_KEY')
    data = pd.DataFrame()
    with FCXMContextManager(access_token=access_token, log_level='error', server='demo',
                            log_file=os.environ['TRADING_FXCM_LOGS_PATH']) as conn:
        data = conn.get_candles(symbol, period=period, columns=['askopen', 'askclose', 'askhigh', 'asklow', 'tickqty'],
                                with_index=False, start=start, end=end)
        # We rename columns this way because it appears that the column order in API response can change
        for col in ['askopen', 'askclose', 'askhigh', 'asklow']:
            data[col[len('ask'):]] = data[col]
            del data[col]
        data['symbol'] = symbol

        # For whatever reason sometimes high and low are not the lowest and the highest
        data['high'] = data[['open', 'close', 'low', 'high']].max(axis=1)
        data['low'] = data[['open', 'close', 'low', 'high']].min(axis=1)

    if data.empty:
        logger.warning('No data has been retrieved')
    return data


def get_candles_all_symbols(start: str, end: str) -> pd.DataFrame:
    candles = pd.DataFrame()
    end = add_days_to_date(end, 1)
    for symb in SYMBOLS:
        candles_tmp = get_candles(symb, start=start, end=end)
        candles = pd.concat([candles, candles_tmp], axis=0)
    candles.reset_index(inplace=True, drop=True)
    return candles


def upload_to_db_candles(start: str, end: str) -> None:
    schema = 'trading'
    uri = get_uri_db(schema=schema)
    nb_days_one_chunk = 30
    periods = split_period_by_chunk(start, end, nb_days_one_chunk)

    for p in periods:
        start_date = p[0]
        end_date = p[1]
        candles = get_candles_all_symbols(start_date, end_date)
        insert_df_to_db(uri, candles, 'candle', schema)










