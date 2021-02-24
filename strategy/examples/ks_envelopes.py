from strategy.strategy import StrategyAbstract, StrategyAction
from indicator.trend import MovingAverage


class KsEnvelopes(StrategyAbstract):
    def apply_strategy(self, update_stop_loss=False):
        self.data = self.data.copy()
        ma_high = MovingAverage(self.data, 'high')
        self.data['ma_high'] = ma_high.compute(span=700)

        ma_low = MovingAverage(self.data, 'low')
        self.data['ma_low'] = ma_low.compute(span=700)

        self.data.dropna(axis=0, inplace=True)
        self.data.reset_index(drop=True, inplace=True)

        self._reinit_data()
        self.stop_loss.data = self.data

        prev_row = None
        in_ma_zone = False
        for row in self.data.itertuples(index=True):
            if prev_row is None:
                self._process_first_trade(row)
            elif self.position == StrategyAction.DO_NOTHING.value:
                if not in_ma_zone and row.close > row.ma_low and row.close < row.ma_high:
                    in_ma_zone = True
                    self._take_no_position(row)
                elif in_ma_zone and row.close > row.ma_high:
                    in_ma_zone = False
                    stop_loss, take_profit = self.stop_loss.compute(row.Index, row.close, buy_action=True)
                    self._take_buy(row, row.close, stop_loss, take_profit)
                elif in_ma_zone and row.close < row.ma_low:
                    in_ma_zone = False
                    stop_loss, take_profit = self.stop_loss.compute(row.Index, row.close, buy_action=False)
                    self._take_sell(row, row.close, stop_loss, take_profit)
                else:
                    self._take_no_position(row)
            else:
                action, action_price, ret, self.position, take_profit, stop_loss = self._quit_position(self.position, row, take_profit, stop_loss, update_stop_loss)
                self._add_one_result_step(action, action_price, ret, take_profit, stop_loss)

            prev_row = row

        self._save_strategy_result()

