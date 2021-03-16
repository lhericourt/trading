import numpy as np

from strategy.strategy import StrategyAbstract
from indicator.trend import HullMovingAverage


class HullRSI(StrategyAbstract):
    def apply_strategy(self, span=14, spread=0):
        self.data = self.data.copy()
        # We compute RSI using Hull average instead of smooth average
        delta = self.data['close'] - self.data['close'].shift(1)
        self.data['delta_pos'] = np.where(delta >= 0, delta, 0)
        self.data['delta_neg'] = np.where(delta < 0, abs(delta), 0)
        self.data['delta_hull_pos'] = HullMovingAverage(self.data, col='delta_pos').compute(span)
        self.data['delta_hull_neg'] = HullMovingAverage(self.data, col='delta_neg').compute(span)
        self.data['rs'] = self.data['delta_hull_pos'] / self.data['delta_hull_neg']
        self.data['rs'].replace([np.inf, -np.inf], 1e10, inplace=True)
        self.data['hull_rsi'] = 100 - 100 / (1 + self.data['rs'])

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

            if all([x.hull_rsi > 10 for x in self.prev_rows]) and row.hull_rsi < 10:
                self.buy_signal = True
            else:
                self.buy_signal = False
            if all([x.hull_rsi < 90 for x in self.prev_rows]) and row.hull_rsi > 90:
                self.sell_signal = True
            else:
                self.sell_signal = False

            stop_loss, take_profit = self.make_decision(row, stop_loss, take_profit, spread)
            self._do_common_processes(row, nb_prev, first_rows=False)

        self._save_strategy_result()

