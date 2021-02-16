from tqdm import tqdm

from strategy.strategy import StrategyAbstract, StrategyAction
from indicator.oscillator import Macd
from utils.utils import compute_sign_changement, compute_slope


class MacdStrat(StrategyAbstract):
    def apply_strategy(self, update_stop_loss=False):
        self.data = self.data.copy()

        macd = Macd(self.data)
        self.data['macd'], self.data['signal'], self.data['hist_macd'] = macd.compute()
        self.data['macd_buy'], self.data['macd_sell'] = compute_sign_changement(self.data, 'hist_macd', span=2)
        self.data.dropna(axis=0, inplace=True)
        self.data.reset_index(drop=True, inplace=True)

        possible_idx = self.data[(self.data['macd_buy'] == 1) | (self.data['macd_sell'] == 1)].index.tolist()
        slopes_before = [compute_slope(self.data, i) for i in tqdm(possible_idx)]
        self.data['slope_before'] = 0
        self.data.loc[possible_idx, 'slope_before'] = slopes_before

        self._reinit_data()
        stop_loss = 0
        take_profit = 0
        prev_row = None
        for row in self.data.itertuples(index=False):
            if prev_row is None:
                self._process_first_trade(row)
            elif self.position == StrategyAction.DO_NOTHING.value:
                if prev_row.macd_buy == 1 and prev_row.slope_before > 30:
                    stop_loss, take_profit = self._take_buy(row)
                elif prev_row.macd_sell == 1 and prev_row.slope_before < -30:
                    stop_loss, take_profit = self._take_sell(row)
                else:
                    self._take_no_position(row)
            else:
                action, action_price, ret, self.position, take_profit, stop_loss = self._quit_position(self.position, row, take_profit, stop_loss, update_stop_loss)
                self._add_one_result_step(action, action_price, ret, take_profit, stop_loss)

            prev_row = row
        self._save_strategy_result()
