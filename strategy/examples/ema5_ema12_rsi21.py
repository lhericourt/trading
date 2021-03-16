from strategy.strategy import StrategyAbstract, StrategyAction
from indicator.trend import ExponentialMovingAverage
from indicator.oscillator import Rsi
from utils.utils import compute_sign_changement


class Ema5Ema12Rsi21(StrategyAbstract):
    def apply_strategy(self, update_stop_loss=False):
        self.data = self.data.copy()

        ema = ExponentialMovingAverage(self.data)
        self.data['ema12'] = ema.compute(span=12)
        self.data['ema5'] = ema.compute(span=5)
        self.data['ema5_minus_ema12'] = self.data['ema5'] - self.data['ema12']
        self.data['ema5_minus_ema12_pos'], self.data['ema5_minus_ema12_neg'] = compute_sign_changement(self.data,
                                                                                                     'ema5_minus_ema12',
                                                                                                     span=2)
        rsi = Rsi(self.data)
        self.data['rsi'] = rsi.compute(span=21)

        self.data.dropna(axis=0, inplace=True)
        self.data.reset_index(drop=True, inplace=True)

        self._reinit_data()
        self.stop_loss.data = self.data
        prev_row = None
        for row in self.data.itertuples(index=True):
            if prev_row is None:
                self._process_first_trade(row)
            elif self.position == StrategyAction.DO_NOTHING.value:
                if prev_row.ema5_minus_ema12_pos == 1 and prev_row.rsi > 50:
                    stop_loss, take_profit = self.stop_loss.compute(row.Index, row.close, buy_action=True)
                    self._take_buy(row, row.close, stop_loss, take_profit)
                elif prev_row.ema5_minus_ema12_neg == 1 and prev_row.rsi < 50:
                    stop_loss, take_profit = self.stop_loss.compute(row.Index, row.close, buy_action=False)
                    self._take_sell(row, row.close, stop_loss, take_profit)
                else:
                    self._take_no_position(row)
            else:
                action, action_price, ret, self.position, take_profit, stop_loss = self._quit_position(self.position, row, take_profit, stop_loss, update_stop_loss)
                self._add_one_result_step(action, action_price, ret, take_profit, stop_loss)

            prev_row = row
        self._save_strategy_result()
