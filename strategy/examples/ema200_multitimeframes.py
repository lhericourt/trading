import pandas as pd

from strategy.strategy import StrategyAbstract, StrategyAction
from indicator.trend import ExponentialMovingAverage
from utils.utils import decompose_date, compute_slope


class Ema200MultiTimeframes(StrategyAbstract):
    def apply_strategy(self, stop_loss_pips=1e-3, update_stop_loss=False):
        self.data = self.data.copy()
        self.data1d = self.data[self.data['table'] == 'candle1d']
        ema = ExponentialMovingAverage(self.data1d)
        self.data1d['ema200_1d'] = ema.compute(span=200)
        # If we do not shift data there will be data leak
        self.data1d = pd.concat([self.data1d[['date']], self.data1d.shift(1)[[x for x in self.data1d.columns if x != 'date']]], axis=1)
        self.data1d = decompose_date(self.data1d)

        self.data4h = self.data[self.data['table'] == 'candle4h']
        ema = ExponentialMovingAverage(self.data4h)
        self.data4h['ema200_4h'] = ema.compute(span=200)
        self.data4h = pd.concat([self.data4h[['date']], self.data4h.shift(1)[[x for x in self.data4h.columns if x != 'date']]], axis=1)
        self.data4h = decompose_date(self.data4h)

        self.data1h = self.data[self.data['table'] == 'candle1h']
        ema = ExponentialMovingAverage(self.data1h)
        self.data1h['ema200_1h'] = ema.compute(span=200)
        self.data1h = decompose_date(self.data1h)

        self.data = pd.merge(self.data1h, self.data4h[['date_only', '4h', 'ema200_4h']], on=['date_only', '4h'], how='left')
        self.data = pd.merge(self.data, self.data1d[['date_only', 'ema200_1d']], on=['date_only'], how='left')

        self.data.dropna(axis=0, inplace=True)
        self.data.reset_index(drop=True, inplace=True)

        self._reinit_data()
        self.stop_loss.data = self.data

        prev_row = list()
        enter_pips = 3e-4

        for row in self.data.itertuples(index=True):
            if len(prev_row) < 2:
                self._process_first_trade(row)
            elif self.position == StrategyAction.DO_NOTHING.value:
                if prev_row[0].ema200_1d < prev_row[0].low and prev_row[0].ema200_4h < prev_row[0].low \
                        and prev_row[1].ema200_1d < prev_row[1].low and prev_row[1].ema200_4h < prev_row[1].low \
                        and prev_row[0].ema200_1h > prev_row[0].low and prev_row[1].ema200_1h < prev_row[1].high \
                        and prev_row[1].close > prev_row[1].open \
                        and row.high > prev_row[1].high + enter_pips:
                    slope = compute_slope(self.data, prev_row[1].Index, col='ema200_1h')
                    if slope > 10:
                        stop_loss, take_profit = self.stop_loss.compute(row.Index, row.close, buy_action=True)
                        self._take_buy(row, prev_row[1].high + enter_pips, stop_loss, take_profit)
                    else:
                        self._take_no_position(row)
                elif prev_row[0].ema200_1d > prev_row[0].high and prev_row[0].ema200_4h > prev_row[0].high \
                        and prev_row[1].ema200_1d > prev_row[1].high and prev_row[1].ema200_4h > prev_row[1].high \
                        and prev_row[0].ema200_1h < prev_row[0].high and prev_row[1].ema200_1h > prev_row[1].low \
                        and prev_row[1].close < prev_row[1].open \
                        and row.low < prev_row[1].low - enter_pips:
                    slope = compute_slope(self.data, prev_row[1].Index, col='ema200_1h')
                    if slope < -10:
                        stop_loss, take_profit = self.stop_loss.compute(row.Index, row.close, buy_action=False)
                        self._take_sell(row, prev_row[1].low - enter_pips, stop_loss, take_profit)
                    else:
                        self._take_no_position(row)
                else:
                    self._take_no_position(row)
            else:
                action, action_price, ret, self.position, take_profit, stop_loss = self._quit_position(self.position, row, take_profit, stop_loss, update_stop_loss)
                self._add_one_result_step(action, action_price, ret, take_profit, stop_loss)

            if len(prev_row) < 2:
                prev_row.append(row)
            else:
                prev_row[0] = prev_row[1]
                prev_row[1] = row
        self._save_strategy_result()
