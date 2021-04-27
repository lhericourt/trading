import numpy as np

from strategy.strategy import StrategyAbstract
from indicator.trend import MovingAverage, ExponentialMovingAverage


class Equilibrium(StrategyAbstract):
    def apply_strategy(self, span_ma=5, span_ema=5, spread=0):
        self.data = self.data.copy()
        self.data['ma'] = MovingAverage(self.data, 'close').compute(span_ma)
        self.data['close_minus_ma'] = self.data['close'] - self.data['ma']
        self.data['ema'] = ExponentialMovingAverage(self.data, 'close_minus_ma').compute(span_ema)

        self.data.dropna(axis=0, inplace=True)
        self.data.reset_index(drop=True, inplace=True)

        self._reinit_data()
        self.stop_loss.data = self.data

        nb_prev = 2
        self.prev_rows = nb_prev * [None]

        stop_loss, take_profit = 0, 0

        for row in self.data.itertuples(index=True):
            if row.Index < max(self.stop_loss.min_rows + 1, nb_prev):
                self._do_nothing(row, 0, 0)
                self._do_common_processes(row, nb_prev, first_rows=True)
                continue

            if all([x.ema > -0.001 for x in self.prev_rows]) and row.ema < -0.001:
                self.buy_signal = True
            else:
                self.buy_signal = False
            if all([x.ema < 0.001 for x in self.prev_rows]) and row.ema > 0.001:
                self.sell_signal = True
            else:
                self.sell_signal = False

            stop_loss, take_profit = self.make_decision(row, stop_loss, take_profit, spread)
            self._do_common_processes(row, nb_prev, first_rows=False)

        self._save_strategy_result()

