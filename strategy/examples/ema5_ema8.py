from strategy.strategy import StrategyAbstract, StrategyAction
from indicator.trend import ExponentialMovingAverage
from utils.utils import compute_sign_changement


class Ema5Ema8(StrategyAbstract):
    def apply_strategy(self, stop_loss_pips=1e-3, update_stop_loss=False):
        self.data = self.data.copy()

        ema = ExponentialMovingAverage(self.data)
        self.data['ema8'] = ema.compute(span=8)
        self.data['ema5'] = ema.compute(span=5)
        self.data['ema5_minus_ema8'] = self.data['ema5'] - self.data['ema8']
        self.data['ema5_minus_ema8_pos'], self.data['ema5_minus_ema8_neg'] = compute_sign_changement(self.data,
                                                                                                     'ema5_minus_ema8',
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
                if prev_row.ema5_minus_ema8_pos == 1:
                    stop_loss, take_profit = self._take_buy(row)
                elif prev_row.ema5_minus_ema8_neg == 1:
                    stop_loss, take_profit = self._take_sell(row)
                else:
                    self._take_no_position(row)
            else:
                action, action_price, ret, self.position, take_profit, stop_loss = self._quit_position(self.position, row, take_profit, stop_loss, update_stop_loss)
                self._add_one_result_step(action, action_price, ret, take_profit, stop_loss)

            prev_row = row
        self._save_strategy_result()

        actions = list()
        actions_price = list()
        ret = list()
        stop_loss_list = list()
