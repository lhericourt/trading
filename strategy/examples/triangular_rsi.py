from strategy.strategy import StrategyAbstract, StrategyAction
from indicator.oscillator import Rsi


class TriRSI(StrategyAbstract):
    def apply_strategy(self, span=5, spread=0):
        self.data = self.data.copy()

        rsi_1 = Rsi(self.data)
        self.data['rsi_1'] = rsi_1.compute(span)
        self.data.dropna(axis=0, inplace=True)

        rsi_2 = Rsi(self.data, 'rsi_1')
        self.data['rsi_2'] = rsi_2.compute(span)
        self.data.dropna(axis=0, inplace=True)

        rsi_3 = Rsi(self.data, 'rsi_2')
        self.data['rsi_3'] = rsi_3.compute(span)
        self.data.dropna(axis=0, inplace=True)
        self.data.reset_index(drop=True, inplace=True)

        self._reinit_data()
        self.stop_loss.data = self.data

        nb_prev = 3
        self.prev_rows = nb_prev * [None]

        stop_loss, take_profit = 0, 0

        for row in self.data.itertuples(index=True):
            if row.Index < max(self.stop_loss.min_rows + 1, nb_prev):
                self._do_nothing(row, 0, 0)
                self._do_common_processes(row, nb_prev, first_rows=True)
                continue

            if all([x.rsi_3 > 30 for x in self.prev_rows]) and row.rsi_3 < 30:
                self.buy_signal = True
            else:
                self.buy_signal = False
            if all([x.rsi_3 < 70 for x in self.prev_rows]) and row.rsi_3 > 70:
                self.sell_signal = True
            else:
                self.sell_signal = False

            stop_loss, take_profit = self.make_decision(row, stop_loss, take_profit, spread)
            self._do_common_processes(row, nb_prev, first_rows=False)

        self._save_strategy_result()

