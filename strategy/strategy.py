from abc import ABC, abstractmethod
from enum import Enum

import pandas as pd

from indicator.performance import CAGR
from indicator.trend import Atr
from indicator.risk import SharpeRatio, Calmar, Volatility


class StrategyAction(Enum):
    DO_NOTHING = 0
    BUY = 1
    SELL = -1


class StrategyAbstract(ABC):
    def __init__(self, data: pd.DataFrame, granularity: int, init_investment: int = 10000,
                 trade_size: float = 0.1) -> None:
        self.data = data.copy().reset_index(drop=True)
        self.granularity = granularity
        self.init_investment = init_investment
        self.trade_size = trade_size * 1e6
        self.indicators = dict()
        self.position = StrategyAction.DO_NOTHING.value

    @abstractmethod
    def apply_strategy(self, **kwargs) -> None:
        pass

    def compute_return(self) -> None:
        self.data['position'] = self.data['action'].cumsum()
        mask = (self.data['action'] != 0) & (self.data['position'] == 0)
        self.data.loc[mask, 'position'] = self.data.loc[mask, 'action'] * -1
        ret = self.data['position'] * (self.data['close'] - self.data['open']) * self.trade_size
        self.data['return'] = ret
        self.data.loc[0, 'return'] = self.init_investment
        self.data['return_cumsum'] = self.data['return'].cumsum()
        return None

    def compute_performance(self) -> None:

        for ind in [CAGR, Volatility, SharpeRatio, Calmar]:
            instance = ind(self.data, 'return_cumsum')
            instance.compute(self.granularity)
            self.indicators[instance.__class__.__name__] = instance.result

        return


class Strategy1(StrategyAbstract):
    def apply_strategy(self, span=20) -> pd.Series:
        atr, _ = Atr(self.data).compute(span=span)

        self.data['atr'] = atr
        self.data['roll_max'] = self.data['high'].rolling(span).max()
        self.data['roll_min'] = self.data['low'].rolling(span).min()
        self.data['roll_max_vol'] = self.data['tickqty'].rolling(span).max()

        previous_data = self.data.shift(1)
        previous_data.columns = ['previous_' + x for x in previous_data.columns]

        self.data = pd.concat([self.data, previous_data], axis=1)

        actions = list()
        for row in self.data.itertuples(index=False):
            if self.position == StrategyAction.DO_NOTHING.value:
                if row.high >= row.roll_max and row.tickqty > 1.5 * row.previous_roll_max_vol:
                    actions.append(StrategyAction.BUY.value)
                    self.position = StrategyAction.BUY.value
                elif row.low <= row.roll_min and row.tickqty > 1.5 * row.previous_roll_max_vol:
                    actions.append(StrategyAction.SELL.value)
                    self.position = StrategyAction.SELL.value
                else:
                    actions.append(StrategyAction.DO_NOTHING.value)
                    self.position = StrategyAction.DO_NOTHING.value

            elif self.position == StrategyAction.BUY.value:
                if row.low < row.previous_close - row.previous_atr:
                    actions.append(StrategyAction.SELL.value)
                    self.position = StrategyAction.DO_NOTHING.value
                else:
                    actions.append(StrategyAction.DO_NOTHING.value)

            elif self.position == StrategyAction.SELL.value:
                if row.high > row.previous_close + row.previous_atr:
                    actions.append(StrategyAction.BUY.value)
                    self.position = StrategyAction.DO_NOTHING.value
                else:
                    actions.append(StrategyAction.DO_NOTHING.value)

        # We shift the action, because we pass the order once we did the detection
        actions = [0] + actions[: -1]
        self.data['action'] = actions

        return self.data['action']







