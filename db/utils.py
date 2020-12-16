import os
import logging
from typing import Tuple, Optional

import pandas as pd
import psycopg2
import psycopg2.extras as extras

from utils.utils import get_password, add_days_to_date

logger = logging.getLogger(__name__)


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


def insert_df_to_db(conn: str, df: pd.DataFrame, table_name: str, schema: Optional[str]) -> None:
    logger.info(f"Inserting data into table {table_name}")

    # case connection is represented by a uri
    if type(conn) == str:
        dsn, schema = split_uri_to_dsn_and_schema(conn)
        conn = psycopg2.connect(dsn)

    if schema is None:
        raise ValueError("No schema is specified")

    table_name = schema + '.' + table_name
    tuples = [tuple(x) for x in df.to_numpy()]
    cols = ','.join(list(df.columns))
    query = f'''INSERT INTO {table_name}({cols}) VALUES %s ON CONFLICT DO NOTHING;'''
    with conn.cursor() as cur:
        try:
            extras.execute_values(cur, query, tuples)
            conn.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            logger.error("Error: %s" % error)
            conn.rollback()
    return


def delete_data(conn: str, table_name: str, schema: Optional[str], start_date, end_date) -> None:
    logger.info(f"Delete data from table {table_name}")

    # case connection is represented by a uri
    if type(conn) == str:
        dsn, schema = split_uri_to_dsn_and_schema(conn)
        conn = psycopg2.connect(dsn)

    end_date = add_days_to_date(end_date, 1)
    table_name = schema + '.' + table_name
    query = f'''DELETE FROM {table_name} WHERE date >= %s AND date < %s;'''
    with conn.cursor() as cur:
        try:
            cur.execute(query, (start_date, end_date, ))
            conn.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            logger.error("Error: %s" % error)
            conn.rollback()


