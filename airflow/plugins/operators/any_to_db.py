from typing import Callable

from airflow.models.baseoperator import BaseOperator
from airflow.hooks.postgres_hook import PostgresHook
from airflow.utils.decorators import apply_defaults

from db.utils import insert_df_to_db, delete_data


class AnyToDb(BaseOperator):
    @apply_defaults
    def __init__(self, table_name: str, function: Callable, first_delete: bool = False, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.table_name = table_name
        self.function = function
        self.first_delete = first_delete

    def execute(self, context):
        schema = 'trading'
        date = context['execution_date'].strftime("%Y-%m-%d")
        data = self.function(date, date)

        pg_hook = PostgresHook(postgres_conn_id='trading', schema=schema)
        with pg_hook.get_conn() as conn:
            if self.first_delete:
                delete_data(conn, self.table_name, schema, date, date)
            insert_df_to_db(conn, data, self.table_name, schema)

        return


