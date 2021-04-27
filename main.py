from config.load import load_conf
from db.apply_migration import do_migration
from data.candle import get_candles, upload_to_db_candles, get_candles_all_symbols
from data.economic_calendar import upload_to_db_events, get_events_on_period
from utils.utils import convert_to_number


from config.log import setup_custom_logger
logger = setup_custom_logger(__name__)
load_conf(filepath='config/configuration.yaml')

#import logging
#log = logging.getLogger(__name__)

#do_migration()
res = get_events_on_period('2021-03-16', '2020-03-16')

#upload_to_db_events('2010-01-01', '2020-12-22')

#test = get_candles_all_symbols('2020-12-13', '2020-12-14')
#test = get_candles('EUR/USD', 'm5', '2021-02-09', '2021-02-11')
#print('toto')
#upload_to_db_candles('2020-08-06', '2020-12-22')

print('toto')
