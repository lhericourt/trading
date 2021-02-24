from strategy.strategy import StrategyAbstract, StrategyAction
from indicator.oscillator import Rsi


class TriRSI(StrategyAbstract):
    def apply_strategy(self, update_stop_loss=False):
        self.data = self.data.copy()

        rsi_1 = Rsi(self.data)
        self.data['rsi_1'] = rsi_1.compute(span=5)
        self.data.dropna(axis=0, inplace=True)

        rsi_2 = Rsi(self.data, 'rsi_1')
        self.data['rsi_2'] = rsi_2.compute(span=5)
        self.data.dropna(axis=0, inplace=True)

        rsi_3 = Rsi(self.data)
        self.data['rsi_3'] = rsi_3.compute(span=5)
        self.data.dropna(axis=0, inplace=True)
        self.data.reset_index(drop=True, inplace=True)

        self._reinit_data()
        self.stop_loss.data = self.data

        prev_row = list()

        for row in self.data.itertuples(index=True):
            if row.Index < max(self.stop_loss.min_rows + 1, 2):
                self._process_first_trade(row)
            elif self.position == StrategyAction.DO_NOTHING.value:
                if prev_row[0].rsi_3 > 30 and prev_row[1].rsi_3 > 30 and row.rsi_3 < 30:
                    stop_loss, take_profit = self.stop_loss.compute(row.Index, row.close, buy_action=True)
                    self._take_buy(row, row.close, stop_loss, take_profit)
                elif prev_row[0].rsi_3 < 70 and prev_row[1].rsi_3 < 70 and row.rsi_3 > 70:
                    stop_loss, take_profit = self.stop_loss.compute(row.Index, row.close, buy_action=False)
                    self._take_sell(row, row.close, stop_loss, take_profit)
                else:
                    self._take_no_position(row)
            else:
                action, action_price, ret, self.position, take_profit, stop_loss = self._quit_position(self.position, row, take_profit, stop_loss, update_stop_loss)
                self._add_one_result_step(action, action_price, ret, take_profit, stop_loss)

            if len(prev_row) < 2:
                prev_row.append(row)
            else:
                prev_row[0] = prev_row[1]
                prev_row[1] = row
        self._save_strategy_result()

