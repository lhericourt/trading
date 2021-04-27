import pandas as pd

from strategy.strategy import StrategyAbstract


class DoubleDifferencing(StrategyAbstract):
    def apply_strategy(self, span=2, spread=0):

        self.data = self.data.copy()
        close_and_shift_close = pd.concat([self.data['close'], self.data['close'].shift(span)], axis=1)
        close_and_shift_close.columns = ['close', 'shift_close']
        close_and_shift_close['diff'] = close_and_shift_close['close'] - close_and_shift_close['shift_close']

        diff_and_shift_diff = pd.concat([close_and_shift_close['diff'], close_and_shift_close['diff'].shift(span)], axis=1)
        diff_and_shift_diff.columns = ['diff', 'shift_diff']
        self.data['second_diff'] = diff_and_shift_diff['diff'] - diff_and_shift_diff['shift_diff']

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

            if all([x.second_diff > -0.002 for x in self.prev_rows]) and row.second_diff < -0.002:
                self.buy_signal = True
            else:
                self.buy_signal = False
            if all([x.second_diff < 0.002 for x in self.prev_rows]) and row.second_diff > 0.002:
                self.sell_signal = True
            else:
                self.sell_signal = False

            stop_loss, take_profit = self.make_decision(row, stop_loss, take_profit, spread)
            self._do_common_processes(row, nb_prev, first_rows=False)

        self._save_strategy_result()

