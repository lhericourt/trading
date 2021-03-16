from strategy.strategy import StrategyAbstract
from indicator.trend import BollingerBands
from indicator.oscillator import Rsi


class MA500Rsi(StrategyAbstract):
    def apply_strategy(self, span_rsi=5, span_ma=500, nb_std_ma=0.5, spread=0):
        self.data = self.data.copy()
        self.data['rsi'] = Rsi(self.data).compute(span_rsi)
        self.data['ma_rsi'], self.data['ma_rsi_up'], self.data['ma_rsi_down'] = BollingerBands(self.data, 'rsi').compute(span_ma, nb_std_ma)

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

            if all([x.rsi > x.ma_rsi_down for x in self.prev_rows]) and row.rsi < row.ma_rsi_down:
                self.buy_signal = True
            else:
                self.buy_signal = False
            if all([x.rsi < x.ma_rsi_up for x in self.prev_rows]) and row.rsi > row.ma_rsi_up:
                self.sell_signal = True
            else:
                self.sell_signal = False

            stop_loss, take_profit = self.make_decision(row, stop_loss, take_profit, spread)
            self._do_common_processes(row, nb_prev, first_rows=False)

        self._save_strategy_result()

