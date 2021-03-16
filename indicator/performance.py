from typing import Union, Dict

import numpy as np
import plotly.graph_objects as go

from indicator.indicator import IndicatorAbstract
from utils.utils import AnnualGranularity


class CAGR(IndicatorAbstract):
    def compute(self, annual_granularity: int = AnnualGranularity.D_1.value) -> float:
        # Be careful only for daily data
        daily_return = self.data[self.col].pct_change()
        cum_return = (1 + daily_return).cumprod()
        n = len(daily_return) / annual_granularity
        self.result = round((cum_return.values[-1])**(1/n) - 1, 2)
        return self.result

    def plot(self, fig) -> go.Figure:
        pass


class Expectancy(IndicatorAbstract):
    def compute(self, trade_size) -> Dict[str, Union[int, float]]:
        wins, losses = list(), list()
        idx_wins_sell, idx_losses_sell, idx_wins_buy, idx_losses_buy = list(), list(), list(), list()
        init_action_price = None
        is_buying = False
        is_selling = False
        prev_candle = None
        idx_init = None
        for candle in self.data.itertuples():
            if not is_buying and not is_selling:
                if candle.action == 1:
                    is_buying = True
                    init_action_price = candle.action_price
                    idx_init = candle.Index
                elif candle.action == -1:
                    is_selling = True
                    init_action_price = candle.action_price
                    idx_init = candle.Index
            elif is_buying:
                if candle.action in (0, -1):
                    is_buying = False
                    if init_action_price < prev_candle.action_price:
                        wins.append(prev_candle.action_price - init_action_price)
                        idx_wins_buy.append(idx_init)
                    else:
                        losses.append(init_action_price - prev_candle.action_price)
                        idx_losses_buy.append(idx_init)
                if candle.action == -1:
                    is_selling = True
                    init_action_price = candle.action_price
                    idx_init = candle.Index
            elif is_selling:
                if candle.action in (0, 1):
                    is_selling = False
                    if init_action_price > prev_candle.action_price:
                        wins.append(init_action_price - prev_candle.action_price)
                        idx_wins_sell.append(idx_init)
                    else:
                        losses.append(prev_candle.action_price - init_action_price)
                        idx_losses_sell.append(idx_init)
                if candle.action == 1:
                    is_buying = True
                    init_action_price = candle.action_price
                    idx_init = candle.Index
            prev_candle = candle

        nb_trades = len(wins + losses)
        prct_winning = len(wins) / nb_trades
        expectancy = np.mean(wins) * prct_winning - np.mean(losses) * (1 - prct_winning)
        profit_factor = float(np.sum(wins) / np.sum(losses))

        prct_winning = round(100 * prct_winning, 1)
        expectancy = round(expectancy * trade_size, 2)
        profit_factor = round(profit_factor, 2)
        self.result = {'NbTrades': nb_trades,
                       'HitRatio': prct_winning,
                       'Expectancy': expectancy,
                       'ProfitFactor': profit_factor,
                       'MeanWinsPips': round(1e4 * np.mean(wins), 1),
                       'MeanLossesPips': round(1e4 * np.mean(losses), 1),
                       'idx_wins_buy': idx_wins_buy,
                       'idx_wins_sell': idx_wins_sell,
                       'idx_losses_buy': idx_losses_buy,
                       'idx_losses_sell': idx_losses_sell}

        return self.result

    def plot(self, fig) -> go.Figure:
        pass