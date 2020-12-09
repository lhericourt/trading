import os
from typing import Tuple, List, Optional
from pathlib import Path
from datetime import datetime, timedelta
import re


def get_password(env_variable: str) -> str:
    password_path = os.environ[env_variable]
    return Path(password_path).read_text()


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



