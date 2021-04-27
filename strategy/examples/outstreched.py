from strategy.strategy import StrategyAbstract, StrategyAction
from indicator.oscillator import Outstreched


class OutstrechedStrategy(StrategyAbstract):
    def apply_strategy(self, col='close', momentum_span=3, ma_span=5, spread=0):
        self.data = self.data.copy()
        outs = Outstreched(self.data, col)
        self.data['outstreched'] = outs.compute(momentum_span, ma_span)
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

            if all([x.outstreched > -2 for x in self.prev_rows]) and row.outstreched < -2:
                self.buy_signal = True
            else:
                self.buy_signal = False
            if all([x.outstreched < 2 for x in self.prev_rows]) and row.outstreched > 2:
                self.sell_signal = True
            else:
                self.sell_signal = False

            stop_loss, take_profit = self.make_decision(row, stop_loss, take_profit, spread)
            self._do_common_processes(row, nb_prev, first_rows=False)

        self._save_strategy_result()

