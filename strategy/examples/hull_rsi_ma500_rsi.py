import numpy as np

from strategy.strategy import StrategyAbstract
from indicator.trend import HullMovingAverage
from indicator.trend import BollingerBands
from indicator.oscillator import Rsi


class HullRSIMA500RSI(StrategyAbstract):
    def apply_strategy(self, span_hull=6, span_rsi=5, span_ma=500, nb_std_ma=0.5, spread=0):
        self.data = self.data.copy()
        # We compute RSI using Hull average instead of smooth average
        delta = self.data['close'] - self.data['close'].shift(1)
        self.data['delta_pos'] = np.where(delta >= 0, delta, 0)
        self.data['delta_neg'] = np.where(delta < 0, abs(delta), 0)
        self.data['delta_hull_pos'] = HullMovingAverage(self.data, col='delta_pos').compute(span_hull)
        self.data['delta_hull_neg'] = HullMovingAverage(self.data, col='delta_neg').compute(span_hull)
        self.data['rs'] = self.data['delta_hull_pos'] / self.data['delta_hull_neg']
        self.data['rs'].replace([np.inf, -np.inf], 1e10, inplace=True)
        self.data['hull_rsi'] = 100 - 100 / (1 + self.data['rs'])

        self.data['rsi'] = Rsi(self.data).compute(span_rsi)
        self.data['ma_rsi'], self.data['ma_rsi_up'], self.data['ma_rsi_down'] = BollingerBands(self.data, 'rsi').compute(span_ma, nb_std_ma)

        self.data.dropna(axis=0, inplace=True)
        self.data.reset_index(drop=True, inplace=True)

        self._reinit_data()
        self.stop_loss.data = self.data

        nb_prev = 2
        self.prev_rows = nb_prev * [None]

        stop_loss, take_profit = 0, 0
        prev_buy_signal_hull = False
        prev_sell_signal_hull = False
        prev_buy_signal_ma = False
        prev_sell_signal_ma = False
        buy_signal_hull = False
        sell_signal_hull = False
        buy_signal_ma = False
        sell_signal_ma = False
        for row in self.data.itertuples(index=True):
            if row.Index < max(self.stop_loss.min_rows + 1, nb_prev):
                self._do_nothing(row, 0, 0)
                self._do_common_processes(row, nb_prev, first_rows=True)
                continue

            if all([x.hull_rsi > 10 for x in self.prev_rows]) and row.hull_rsi < 10:
                buy_signal_hull = True
            else:
                buy_signal_hull = False
            if all([x.hull_rsi < 90 for x in self.prev_rows]) and row.hull_rsi > 90:
                sell_signal_hull = True
            else:
                sell_signal_hull = False

            if all([x.rsi > x.ma_rsi_down for x in self.prev_rows]) and row.rsi < row.ma_rsi_down:
                buy_signal_ma = True
            else:
                buy_signal_ma = False
            if all([x.rsi < x.ma_rsi_up for x in self.prev_rows]) and row.rsi > row.ma_rsi_up:
                sell_signal_ma = True
            else:
                sell_signal_ma = False

            if (buy_signal_hull and buy_signal_ma) or (buy_signal_hull and prev_buy_signal_ma) or (prev_buy_signal_hull and buy_signal_ma):
                self.buy_signal = True
            else:
                self.buy_signal = False

            if (sell_signal_hull and sell_signal_ma) or (sell_signal_hull and prev_sell_signal_ma) or (prev_sell_signal_hull and sell_signal_ma):
                self.sell_signal = True
            else:
                self.sell_signal = False

            stop_loss, take_profit = self.make_decision(row, stop_loss, take_profit, spread)
            self._do_common_processes(row, nb_prev, first_rows=False)
            prev_buy_signal_hull = buy_signal_hull
            prev_sell_signal_hull = sell_signal_hull
            prev_buy_signal_ma = buy_signal_ma
            prev_sell_signal_ma = sell_signal_ma

        self._save_strategy_result()

