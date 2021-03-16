from typing import Tuple, Optional
from abc import ABC, abstractmethod

from indicator.oscillator import Atr


class StopLoss(ABC):
    def __init__(self, column: str = 'close', min_rows: int = 0, update: bool = False):
        self.data = None
        self.column = column
        self.min_rows = min_rows
        self.update = update

    @abstractmethod
    def compute(self, index: int, price: float, buy_action: bool = True, spread: float = 0):
        pass


class StopLossFix(StopLoss):
    def __init__(self, stop: float = 5e-4, profit: float = 5e-3, column: str = 'close', min_rows: int = 0):
        self.stop = stop
        self.profit = profit
        super().__init__(column, min_rows)

    def compute(self, index: int, price: float, buy_action: bool = True) -> Tuple[float, float]:
        if buy_action:
            stop_loss = price - self.stop
            take_profit = price + self.profit
        else:
            stop_loss = price + self.stop
            take_profit = price - self.profit

        return stop_loss, take_profit


class StopLossWithConstraint(StopLoss):
    def __init__(self, stop: float = 5e-4, profit: float = 5e-3, column: str = 'close', min_rows: int = 0):
        self.stop = stop
        self.profit = profit
        super().__init__(column, min_rows)

    def compute(self, index: int, price: float, buy_action: bool = True) -> Tuple[float, float]:
        constraint = float(self.data.loc[index, self.column])
        if buy_action:
            stop_loss = min(price - self.stop, constraint)
            take_profit = price + self.profit
        else:
            stop_loss = max(price + self.stop, constraint)
            take_profit = price - self.profit

        return stop_loss, take_profit


class StopLossATR(StopLoss):
    def __init__(self, span: int = 14, stop: int = 1, profit: int = 4, column: str = 'close', update: bool = False):
        self.span = span
        self.stop = stop
        self.profit = profit
        super().__init__(column, span, update)

    def compute(self, index: int, price: float, buy_action: bool = True, spread: float = 0) -> \
            Tuple[Optional[float], Optional[float]]:
        tmp_data = self.data.loc[index - 2 * self.span: index, :]
        atr = Atr(tmp_data, self.column)
        atr.compute(self.span, avg_type='ewm')
        atr_val = atr.result[0][-1]
        if buy_action:
            stop_loss = price - self.stop * atr_val + spread
            if stop_loss > price:
                return None, None
            take_profit = price + self.profit * atr_val
        else:
            stop_loss = price + self.stop * atr_val - spread
            if stop_loss < price:
                return None, None
            take_profit = price - self.profit * atr_val
        return stop_loss, take_profit



