from strategy.strategy import StrategyAbstract
from indicator.oscillator import Macd
from indicator.transformation import Fisher


class MACDFlipStrategy(StrategyAbstract):
    def apply_strategy(self, span_fast: int = 12, span_slow: int = 26, span_signal: int = 9):
        self.data = self.data.copy()
        macd = Macd(self.data)
        self.data['macd_line'], self.data['macd_signal'], _ = macd.compute(span_fast, span_slow, span_signal)

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

            if all([x.macd_line < 0 for x in self.prev_rows]) and row.macd_line > 0:
                self.buy_signal = True
            else:
                self.buy_signal = False

            if all([x.macd_line > 0 for x in self.prev_rows]) and row.macd_line < 0:
                self.sell_signal = True
            else:
                self.sell_signal = False

            stop_loss, take_profit = self.make_decision(row, stop_loss, take_profit)
            self._do_common_processes(row, nb_prev, first_rows=False)

        self._save_strategy_result()

