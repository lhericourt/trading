from abc import ABC, abstractmethod
from enum import Enum
from typing import Tuple

import pandas as pd

from indicator.performance import CAGR, Expectancy
from strategy.stop_loss import StopLoss
from indicator.risk import SharpeRatio, Calmar, Volatility, RiskRewardRatio


class StrategyAction(Enum):
    DO_NOTHING = 0
    BUY = 1
    SELL = -1


class StrategyAbstract(ABC):
    def __init__(self, data: pd.DataFrame, granularity: int, stop_loss: StopLoss, init_investment: int = 10000,
                 trade_size: float = 0.1) -> None:
        self.data = data.copy().reset_index(drop=True)
        self.granularity = granularity
        self.init_investment = init_investment
        self.trade_size = trade_size * 1e6
        self.indicators = dict()
        self.position = StrategyAction.DO_NOTHING.value
        self.stop_loss = stop_loss
        self.actions = list()
        self.actions_price = list()
        self.ret = list()
        self.stop_loss_list = list()
        self.take_profit_list = list()

    @abstractmethod
    def apply_strategy(self, **kwargs) -> None:
        pass

    def compute_return(self) -> None:
        self.data['return'] = self.data['ret'] * self.trade_size
        self.data.loc[0, 'return'] = self.init_investment
        self.data['return_cumsum'] = self.data['return'].cumsum()
        return None

    def compute_performance(self) -> None:
        for ind in [CAGR, Volatility, SharpeRatio, Calmar]:
            instance = ind(self.data, 'return_cumsum')
            instance.compute(self.granularity)
            self.indicators[instance.__class__.__name__] = instance.result

        for ind in [RiskRewardRatio]:
            instance = ind(self.data)
            instance.compute()
            for ind_name, val in instance.result.items():
                self.indicators[ind_name] = val

        for ind in [Expectancy]:
            instance = ind(self.data)
            instance.compute(self.trade_size)
            for ind_name, val in instance.result.items():
                self.indicators[ind_name] = val

        return None

    def _process_first_trade(self, candle) -> None:
        self.actions.append(StrategyAction.DO_NOTHING.value)
        self.actions_price.append(candle.close)
        self.ret.append(0)
        self.stop_loss_list.append(0)
        self.take_profit_list.append(0)
        return

    def _take_buy(self, candle: pd.DataFrame, price: float, stop_loss: float, take_profit: float) -> Tuple[float, float]:
        self.actions.append(StrategyAction.BUY.value)
        self.stop_loss_list.append(stop_loss)
        self.take_profit_list.append(take_profit)
        self.position = StrategyAction.BUY.value
        self.actions_price.append(price)
        self.ret.append(candle.close - price)
        return stop_loss, take_profit

    def _take_sell(self, candle: pd.DataFrame, price: float, stop_loss: float, take_profit: float) -> Tuple[float, float]:
        self.actions.append(StrategyAction.SELL.value)
        self.stop_loss_list.append(stop_loss)
        self.take_profit_list.append(take_profit)
        self.position = StrategyAction.SELL.value
        self.actions_price.append(price)
        self.ret.append(price - candle.close)
        return stop_loss, take_profit

    def _take_no_position(self, candle: pd.DataFrame) -> None:
        self.actions.append(StrategyAction.DO_NOTHING.value)
        self.position = StrategyAction.DO_NOTHING.value
        self.stop_loss_list.append(0)
        self.take_profit_list.append(0)
        self.actions_price.append(candle.close)
        self.ret.append(0)
        return

    def _quit_position(self, position: int, candle: pd.DataFrame, take_profit: float, stop_loss: float,
                       update_stop_loss: bool = False) -> Tuple[int, float, float, int, float, float]:
        action, action_price = StrategyAction.DO_NOTHING.value, candle.close
        ret = candle.close - candle.open if position == StrategyAction.BUY.value else candle.open - candle.close
        next_position = position
        if position == StrategyAction.BUY.value:
            if candle.low < stop_loss or candle.high > take_profit:
                action = StrategyAction.SELL.value
                next_position = StrategyAction.DO_NOTHING.value
                if candle.low < stop_loss:
                    action_price = stop_loss
                    ret = stop_loss - candle.open
                else:
                    action_price = take_profit
                    ret = take_profit - candle.open
                take_profit, stop_loss = 0, 0

            elif update_stop_loss and candle.low - self.stop_loss_pips > stop_loss:
                stop_loss = candle.low - self.stop_loss_pips

        elif position == StrategyAction.SELL.value:
            if candle.high > stop_loss or candle.low < take_profit:
                action = StrategyAction.BUY.value
                next_position = StrategyAction.DO_NOTHING.value
                if candle.high > stop_loss:
                    action_price = stop_loss
                    ret = candle.open - stop_loss
                else:
                    action_price = take_profit
                    ret = candle.open - take_profit
                take_profit, stop_loss = 0, 0

            elif update_stop_loss and candle.high + self.stop_loss_pips < stop_loss:
                stop_loss = candle.high + self.stop_loss_pips

        return action, action_price, ret, next_position, take_profit, stop_loss

    def _reinit_data(self) -> None:
        self.position = StrategyAction.DO_NOTHING.value
        self.actions = list()
        self.actions_price = list()
        self.ret = list()
        self.stop_loss_list = list()
        self.take_profit_list = list()
        return

    def _add_one_result_step(self, action: int, action_price: float, ret: float, take_profit: float,
                             stop_loss: float) -> None:
        self.actions.append(action)
        self.actions_price.append(action_price)
        self.ret.append(ret)
        self.take_profit_list.append(take_profit)
        self.stop_loss_list.append(stop_loss)
        return

    def _save_strategy_result(self) -> None:
        self.data['action'] = self.actions
        self.data['action_price'] = self.actions_price
        self.data['ret'] = self.ret
        self.data['stop_loss'] = self.stop_loss_list
        self.data['take_profit'] = self.take_profit_list
        return
