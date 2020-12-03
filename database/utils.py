import os
import logging
from typing import Tuple, Optional

import pandas as pd
import psycopg2
import psycopg2.extras as extras

from utils.utils import get_password

logger = logging.getLogger('root')


def get_uri_db(schema: str = None) -> str:
    password = get_password('TRADING_DB_PASSWORD_PATH')

    uri = f"postgres://{os.environ['TRADING_DB_USER']}:{password}@" \
          f"{os.environ['TRADING_DB_HOST']}:{os.environ['TRADING_DB_PORT']}/" \
          f"{os.environ['TRADING_DB_NAME']}"

    if schema:
        uri += "?schema=" + schema

    return uri


def split_uri_to_dsn_and_schema(uri: str) -> Tuple[str, Optional[str]]:
    res = uri.split('?schema=')
    schema = None
    if len(res) > 1:
        schema = res[1]
    return res[0], schema


def insert_df_to_db(uri: str, df: pd.DataFrame, table_name: str) -> None:
    logger.info(f"Inserting data into table {table_name}")
    dsn, schema = split_uri_to_dsn_and_schema(uri)
    if schema is None:
        raise ValueError("No schema is specified")

    table_name = schema + '.' + table_name
    tuples = [tuple(x) for x in df.to_numpy()]
    cols = ','.join(list(df.columns))
    query = f'''INSERT INTO {table_name}({cols}) VALUES %s ON CONFLICT DO NOTHING;'''
    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            try:
                extras.execute_values(cur, query, tuples)
                conn.commit()
            except (Exception, psycopg2.DatabaseError) as error:
                logger.error("Error: %s" % error)
                conn.rollback()
    return
