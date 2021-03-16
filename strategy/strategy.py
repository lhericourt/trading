from abc import ABC, abstractmethod
from enum import Enum
from typing import Tuple, Optional

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
        self.trade_size = trade_size * 1e5
        self.indicators = dict()
        self.position = StrategyAction.DO_NOTHING.value
        self.buy_signal = False
        self.sell_signal = False
        self.current_return = 0
        self.current_returns = list()
        self.prev_rows = list()
        self.buy_signals = list()
        self.sell_signals = list()
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

    def _do_common_processes(self, candle: pd.DataFrame, nb_prev: int, first_rows: bool = False) -> None:
        if first_rows and candle.Index < nb_prev:
            self.prev_rows[candle.Index] = candle
        else:
            del self.prev_rows[0]
            self.prev_rows.append(candle)

        self.buy_signals.append(self.buy_signal)
        self.sell_signals.append(self.sell_signal)

        return None

    def _take_buy(self, candle: pd.DataFrame, price: float, stop_loss: float, take_profit: float, spread: float) -> float:
        self.actions.append(StrategyAction.BUY.value)
        self.stop_loss_list.append(stop_loss)
        self.take_profit_list.append(take_profit)
        self.position = StrategyAction.BUY.value
        self.actions_price.append(price)
        self.ret.append(candle.close - price - spread)
        self.position = StrategyAction.BUY.value
        self.current_return += candle.close - price - spread
        self.current_returns.append(self.current_return)
        return candle.close - price

    def _take_sell(self, candle: pd.DataFrame, price: float, stop_loss: float, take_profit: float, spread: float) -> float:
        self.actions.append(StrategyAction.SELL.value)
        self.stop_loss_list.append(stop_loss)
        self.take_profit_list.append(take_profit)
        self.position = StrategyAction.SELL.value
        self.actions_price.append(price)
        self.ret.append(price - candle.close - spread)
        self.position = StrategyAction.SELL.value
        self.current_return += price - candle.close - spread
        self.current_returns.append(self.current_return)
        return price - candle.close

    def _quit_buy(self, candle: pd.DataFrame, take_profit: float, stop_loss: float):
        self.actions.append(self.position)
        action_price = stop_loss if candle.low < stop_loss else candle.close
        self.actions_price.append(action_price)
        self.stop_loss_list.append(stop_loss)
        self.take_profit_list.append(take_profit)
        self.ret.append(action_price - candle.open)
        self.position = StrategyAction.DO_NOTHING.value
        self.current_return += action_price - candle.open
        self.current_returns.append(self.current_return)
        self.current_return = 0

    def _quit_sell(self, candle: pd.DataFrame, take_profit: float, stop_loss: float):
        self.actions.append(self.position)
        action_price = stop_loss if candle.high > stop_loss else candle.close
        self.actions_price.append(action_price)
        self.stop_loss_list.append(stop_loss)
        self.take_profit_list.append(take_profit)
        self.ret.append(candle.open - action_price)
        self.position = StrategyAction.DO_NOTHING.value
        self.current_return += candle.open - action_price
        self.current_returns.append(self.current_return)
        self.current_return = 0

    def _do_nothing(self, candle: pd.DataFrame, take_profit: Optional[float], stop_loss: Optional[float]):
        self.actions.append(self.position)
        self.actions_price.append(candle.close)
        if self.position == StrategyAction.DO_NOTHING.value:
            self.stop_loss_list.append(0)
            self.take_profit_list.append(0)
            self.ret.append(0)
            self.current_returns.append(0)
        elif self.position == StrategyAction.BUY.value:
            self.stop_loss_list.append(stop_loss)
            self.take_profit_list.append(take_profit)
            self.ret.append(candle.close - candle.open)
            self.current_return += candle.close - candle.open
            self.current_returns.append(self.current_return)
        elif self.position == StrategyAction.SELL.value:
            self.stop_loss_list.append(stop_loss)
            self.take_profit_list.append(take_profit)
            self.ret.append(candle.open - candle.close)
            self.current_return += candle.open - candle.close
            self.current_returns.append(self.current_return)

        return

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
        self.data['buy_signal'] = self.buy_signals
        self.data['sell_signal'] = self.sell_signals
        self.data['action_price'] = self.actions_price
        self.data['ret'] = self.ret
        self.data['stop_loss'] = self.stop_loss_list
        self.data['take_profit'] = self.take_profit_list
        self.data['current_returns'] = self.current_returns
        return

    def make_decision(self, candle: pd.DataFrame, stop_loss: float, take_profit: float, spread: float) -> Tuple[float,
                                                                                                                float]:
        if self.position == StrategyAction.DO_NOTHING.value and self.buy_signal:
            stop_loss, take_profit = self.stop_loss.compute(candle.Index, candle.close, buy_action=True, spread=spread)
            if stop_loss is None:
                self._do_nothing(candle, take_profit, stop_loss)
            else:
                self._take_buy(candle, candle.close, stop_loss, take_profit, spread)
        elif self.position == StrategyAction.DO_NOTHING.value and self.sell_signal:
            stop_loss, take_profit = self.stop_loss.compute(candle.Index, candle.close, buy_action=False, spread=spread)
            if stop_loss is None:
                self._do_nothing(candle, take_profit, stop_loss)
            else:
                self._take_sell(candle, candle.close, stop_loss, take_profit, spread)
        elif self.position == StrategyAction.BUY.value and (self.sell_signal or candle.low < stop_loss
                                                            or candle.high > take_profit):
            self._quit_buy(candle, take_profit, stop_loss)
        elif self.position == StrategyAction.SELL.value and (self.buy_signal or candle.high > stop_loss
                                                             or candle.low < take_profit):
            self._quit_sell(candle, take_profit, stop_loss)
        elif self.position in (StrategyAction.BUY.value, StrategyAction.SELL.value):
            if self.stop_loss.update:
                buy_action = True if self.position == StrategyAction.BUY.value else False
                new_stop_loss, _ = self.stop_loss.compute(candle.Index, candle.close, buy_action)
                if buy_action and new_stop_loss > stop_loss or not buy_action and new_stop_loss < stop_loss:
                    stop_loss = new_stop_loss
            self._do_nothing(candle, take_profit, stop_loss)
        else:
            self._do_nothing(candle, take_profit, stop_loss)

        return stop_loss, take_profit
