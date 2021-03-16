from strategy.strategy import StrategyAbstract, StrategyAction
from indicator.oscillator import Rsi
from indicator.transformation import Fisher


class FisherRSI(StrategyAbstract):
    def apply_strategy(self, update_stop_loss=False):
        self.data = self.data.copy()
        fisher = Fisher(self.data)
        self.data['fisher'] = fisher.compute(span=10)
        self.data.dropna(axis=0, inplace=True)

        rsi = Rsi(self.data, col='fisher')
        self.data['rsi'] = rsi.compute(span=5)

        self.data.dropna(axis=0, inplace=True)
        self.data.reset_index(drop=True, inplace=True)

        self._reinit_data()
        self.stop_loss.data = self.data

        nb_prev = 5
        self.prev_rows = nb_prev * [None]

        stop_loss, take_profit = 0, 0

        for row in self.data.itertuples(index=True):
            if row.Index < max(self.stop_loss.min_rows + 1, nb_prev):
                self._do_nothing(row, 0, 0)
                self._do_common_processes(row, nb_prev, first_rows=True)
                continue

            if all([x.rsi > 25 for x in self.prev_rows]) and row.rsi < 25:
                self.buy_signal = True
            else:
                self.buy_signal = False
            if all([x.rsi < 75 for x in self.prev_rows]) and row.rsi > 75:
                self.sell_signal = True
            else:
                self.sell_signal = False

            stop_loss, take_profit = self.make_decision(row, stop_loss, take_profit)
            self._do_common_processes(row, nb_prev, first_rows=False)

        self._save_strategy_result()

