import logging
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup, Tag
from cerberus import Validator
import pandas as pd

from utils.utils import convert_to_number, split_period_by_chunk
from db.utils import get_uri_db, insert_df_to_db, delete_data

logger = logging.getLogger(__name__)

schema = {
    'time': {'type': 'string', 'nullable': False, 'regex': r'^\d{2}:\d{2}$'},
    'country': {'type': 'string', 'nullable': False, 'allowed': ['AUD', 'HKD', 'USD', 'EUR', 'CAD', 'JPY', 'CHF', 'GBP']},
    'importance': {'type': 'integer', 'nullable': False, 'min': 1, 'max': 3},
    'name': {'type': 'string', 'nullable': False},
    'actual_value': {'type': 'float', 'nullable': True},
    'is_positive': {'type': 'integer', 'nullable': False, 'min': -1, 'max': 1},
    'forecast_value': {'type': 'float', 'nullable': True},
    'previous_value': {'type': 'float', 'nullable': True}
}

url = 'https://fr.investing.com/economic-calendar/Service/getCalendarFilteredData'
max_event_per_request = 200
time_zone_gmt0 = '55'
countries_id = {'australia_id': '25',
                'hong-kong_id': '39',
                'us_id': '5',
                'europe_id': '72',
                'canada_id': '6',
                'japan_id': '35',
                'switzerland_id': '12',
                'united_kingdom_id': '4'}

header = {
    'Host': 'fr.investing.com',
    'Connection': 'keep-alive',
    'Content-Length': '235',
    'Accept': '*/*',
    'X-Requested-With': 'XMLHttpRequest',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Origin': 'https://fr.investing.com',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Dest': 'empty',
    'Referer': 'https://fr.investing.com/economic-calendar/',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7'
}


def parse_event_html(event: Tag) -> Optional[Dict]:
    res = dict()
    res['time'] = event.find(class_='time').get_text().strip()
    res['country'] = event.find(class_='flagCur').get_text().strip()
    importance = event.find(class_='sentiment').get('title').strip()
    if 'faible' in importance.lower():
        res['importance'] = 1
    elif 'moyenne' in importance.lower():
        res['importance'] = 2
    elif 'forte' in importance.lower():
        res['importance'] = 3
    res['name'] = event.find(class_='event').get_text().strip()

    actual_value = event.find(class_='act')
    is_positive = 0
    if 'greenFont' in actual_value['class']:
        is_positive = 1
    elif 'redFont' in actual_value['class']:
        is_positive = -1
    res['actual_value'] = convert_to_number(actual_value.get_text().strip())
    res['is_positive'] = is_positive

    res['forecast_value'] = convert_to_number(event.find(class_='fore').get_text().strip())
    res['previous_value'] = convert_to_number(event.find(class_='prev').get_text().strip())

    event_validator = Validator(schema)
    if not event_validator(res):
        for err, reason in event_validator.errors.items():
            logger.info(res)
            logger.info(f'Error on field {err} : {reason}')
        res = None
    return res


def get_events(date: str) -> List[Dict]:
    start_date = date
    end_date = date

    params = [('country[]', c_id) for c_id in countries_id.values()]
    params.extend([('dateFrom', start_date),
                   ('dateTo', end_date),
                   ('timeZone', time_zone_gmt0),
                   ('timeFilter', 'timeRemain'),
                   ('currentTab', 'custom'),
                   ('limit_from', '0')
                   ])

    r = requests.post(url, data=params, headers=header)

    events = list()
    if r.status_code == requests.codes.ok:
        data = r.json()['data']
        soup = BeautifulSoup(data, features='lxml')
        events_html = soup.select('.js-event-item')
        for ev in events_html:
            res = parse_event_html(ev)
            if res:
                res['date'] = date + ' ' + res['time']
                del res['time']
                events.append(res)

    if len(events) >= max_event_per_request:
        logger.warning(f"Missing events for date : {date}")

    logger.info(f"number of events : {len(events)}")

    return events


def get_events_on_period(start_date: str, end_date: str) -> pd.DataFrame:
    periods = split_period_by_chunk(start_date, end_date, chunk_size=1)
    events = list()
    for p in periods:
        events.extend(get_events(p[0]))
    events.extend(get_events(end_date))

    events_df = pd.DataFrame(events)
    events_df = events_df.where(pd.notnull(events_df), None)

    return events_df


def upload_to_db_events(start: str = None, end: str = None) -> None:
    schema = 'trading'
    uri = get_uri_db(schema=schema)
    events = get_events_on_period(start, end)
    delete_data(uri, 'event', schema, start, end)
    insert_df_to_db(uri, events, 'event', schema=schema)
    return None



