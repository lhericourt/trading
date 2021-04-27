from strategy.strategy import StrategyAbstract
from indicator.oscillator import Stochastic, Rsi


class RSIStochastic(StrategyAbstract):
    def apply_strategy(self, span_fast=14, span_slow=3, slow=False, span_rsi=5, spread=0):
        self.data = self.data.copy()
        stoch = Stochastic(self.data)
        self.data['stoch'], self.data['stoch_ma'], self.data['stoch_hist'] = stoch.compute(span_fast, span_slow, slow)
        self.data.dropna(axis=0, inplace=True)
        self.data.reset_index(drop=True, inplace=True)

        rsi = Rsi(self.data, col='stoch_ma')
        self.data['rsi_stoch'] = rsi.compute(span_rsi)
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

            if all([x.stoch_ma > 25 for x in self.prev_rows]) and row.stoch_ma < 25:
                self.buy_signal = True
            else:
                self.buy_signal = False
            if all([x.stoch_ma < 75 for x in self.prev_rows]) and row.stoch_ma > 75:
                self.sell_signal = True
            else:
                self.sell_signal = False

            stop_loss, take_profit = self.make_decision(row, stop_loss, take_profit, spread)
            self._do_common_processes(row, nb_prev, first_rows=False)

        self._save_strategy_result()

