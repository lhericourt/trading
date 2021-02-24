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


class HitRatio(IndicatorAbstract):
    def compute(self) -> Dict[str, Union[int, float]]:
        nb_trades_buy, nb_trades_sell = 0, 0
        nb_winning_trades_buy, nb_winning_trades_sell = 0, 0
        init_action_price = None
        is_buying = False
        is_selling = False
        for candle in self.data.itertuples():
            if not is_buying and not is_selling:
                if candle.action == 1:
                    is_buying = True
                    init_action_price = candle.action_price
                elif candle.action == -1:
                    is_selling = True
                    init_action_price = candle.action_price
            elif is_buying:
                if candle.action == -1:
                    is_buying = False
                    nb_trades_buy += 1
                    if init_action_price < candle.action_price:
                        nb_winning_trades_buy += 1
            elif is_selling:
                if candle.action == 1:
                    is_selling = False
                    nb_trades_sell += 1
                    if init_action_price > candle.action_price:
                        nb_winning_trades_sell += 1

        self.result = {
            'nb_trades': nb_trades_buy + nb_trades_sell,
            'ratio_winning_trades': round(100 * (nb_winning_trades_buy + nb_winning_trades_sell) / (nb_trades_buy + nb_trades_sell), 1),
            'nb_buying_trades': nb_trades_buy,
            'ratio_winning_buying_trades': round(100 * nb_winning_trades_buy / nb_trades_buy, 1),
            'nb_selling_trades': nb_trades_sell,
            'ratio_winning_selling_trades': round(100 * nb_winning_trades_sell / nb_trades_sell, 1)
        }

        return self.result

    def plot(self, fig) -> go.Figure:
        pass


class Expectancy(IndicatorAbstract):
    def compute(self, trade_size) -> Dict[str, Union[int, float]]:
        wins, losses = list(), list()
        init_action_price = None
        is_buying = False
        is_selling = False
        for candle in self.data.itertuples():
            if not is_buying and not is_selling:
                if candle.action == 1:
                    is_buying = True
                    init_action_price = candle.action_price
                elif candle.action == -1:
                    is_selling = True
                    init_action_price = candle.action_price
            elif is_buying:
                if candle.action == -1:
                    is_buying = False
                    if init_action_price < candle.action_price:
                        wins.append(candle.action_price - init_action_price)
                    else:
                        losses.append(init_action_price - candle.action_price)
            elif is_selling:
                if candle.action == 1:
                    is_selling = False
                    if init_action_price > candle.action_price:
                        wins.append(init_action_price - candle.action_price)
                    else:
                        losses.append(candle.action_price - init_action_price)

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
                       'ProfitFactor': profit_factor}

        return self.result

    def plot(self, fig) -> go.Figure:
        pass