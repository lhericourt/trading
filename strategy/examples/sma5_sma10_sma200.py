from strategy.strategy import StrategyAbstract, StrategyAction
from indicator.trend import MovingAverage
from utils.utils import compute_sign_changement


class Sma5Sma10Sma200(StrategyAbstract):
    def apply_strategy(self, stop_loss_pips=1e-3, update_stop_loss=False):
        self.data = self.data.copy()

        sma = MovingAverage(self.data)
        self.data['sma10'] = sma.compute(span=10)
        self.data['sma20'] = sma.compute(span=20)
        self.data['sma200'] = sma.compute(span=200)
        self.data['sma10_minus_sma20'] = self.data['sma10'] - self.data['sma20']
        self.data['sma10_minus_sma20_pos'], self.data['sma10_minus_sma20_neg'] = compute_sign_changement(self.data,
                                                                                                     'sma10_minus_sma20',
                                                                                                     span=2)
        self.data.dropna(axis=0, inplace=True)
        self.data.reset_index(drop=True, inplace=True)

        self._reinit_data()
        stop_loss = 0
        take_profit = 0
        prev_row = None
        for row in self.data.itertuples(index=False):
            if prev_row is None:
                self._process_first_trade(row)
            elif self.position == StrategyAction.DO_NOTHING.value:
                if prev_row.sma10_minus_sma20_pos == 1 and prev_row.close > prev_row.sma200:
                    stop_loss, take_profit = self._take_buy(row)
                elif prev_row.sma10_minus_sma20_neg == 1 and prev_row.close < row.sma200:
                    stop_loss, take_profit = self._take_sell(row)
                else:
                    self._take_no_position(row)
            else:
                action, action_price, ret, self.position, take_profit, stop_loss = self._quit_position(self.position, row, take_profit, stop_loss, update_stop_loss)
                self._add_one_result_step(action, action_price, ret, take_profit, stop_loss)

            prev_row = row
        self._save_strategy_result()
