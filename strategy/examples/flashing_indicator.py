from strategy.strategy import StrategyAbstract
from indicator.trend import BollingerBands


class FlashingIndicator(StrategyAbstract):
    def apply_strategy(self, roc_period=10, bb_span=20, bb_nb_std=2, correl_span=5, use_correl=False):
        self.data = self.data.copy()
        self.data['pct_col'] = self.data['close'].pct_change(periods=roc_period)
        bb = BollingerBands(self.data, 'pct_col')
        _, self.data['bb_up'], self.data['bb_down'] = bb.compute(bb_span, bb_nb_std)

        self.data.dropna(axis=0, inplace=True)
        self.data.reset_index(drop=True, inplace=True)

        self._reinit_data()
        self.stop_loss.data = self.data

        nb_prev = 3
        self.prev_rows = nb_prev * [None]

        stop_loss, take_profit = 0, 0

        for row in self.data.itertuples(index=True):
            if row.Index < max(self.stop_loss.min_rows + 1, nb_prev, correl_span):
                self._do_nothing(row, 0, 0)
                self._do_common_processes(row, nb_prev, first_rows=True)
                continue

            if all([x.pct_col > x.bb_down for x in self.prev_rows]) and row.pct_col < row.bb_down:
                if not use_correl:
                    self.buy_signal = True
                else:
                    auto_corr_value = self.data.loc[row.Index - correl_span + 1: row.Index, 'close'].autocorr(lag=1)
                    if auto_corr_value > 0.95:
                        self.buy_signal = True
                    else:
                        self.buy_signal = False

            else:
                self.buy_signal = False

            if all([x.pct_col < x.bb_up for x in self.prev_rows]) and row.pct_col > row.bb_up:
                if not use_correl:
                    self.sell_signal = True
                else:
                    auto_corr_value = self.data.loc[row.Index - correl_span + 1: row.Index, 'close'].autocorr(lag=1)
                    if auto_corr_value > 0.95:
                        self.sell_signal = True
                    else:
                        self.sell_signal = False
            else:
                self.sell_signal = False

            stop_loss, take_profit = self.make_decision(row, stop_loss, take_profit)
            self._do_common_processes(row, nb_prev, first_rows=False)

        self._save_strategy_result()

