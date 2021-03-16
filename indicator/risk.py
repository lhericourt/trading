from typing import Dict

import plotly.graph_objects as go
import numpy as np

from indicator.indicator import IndicatorAbstract
from indicator.performance import CAGR
from utils.utils import AnnualGranularity


class Volatility(IndicatorAbstract):
    def compute(self, annual_granularity: int = AnnualGranularity.D_1.value) -> float:
        daily_return = self.data[self.col].pct_change()
        self.result = round(daily_return.std() * np.sqrt(annual_granularity), 2)
        return self.result

    def plot(self, fig) -> go.Figure:
        pass


class SharpeRatio(IndicatorAbstract):
    def compute(self,annual_granularity: int = AnnualGranularity.D_1.value,  risk_free_cagr: float = 0.005) -> float:
        cagr = CAGR(self.data, self.col)
        cagr.compute(annual_granularity)

        vol = Volatility(self.data, self.col)
        vol.compute(annual_granularity)
        self.result = round((cagr.result - risk_free_cagr) / vol.result, 2)
        return self.result

    def plot(self, fig) -> go.Figure:
        pass


class MaxDrawDown(IndicatorAbstract):
    def compute(self) -> float:
        ret = self.data[self.col].pct_change()
        cum_return = (1 + ret).cumprod()
        cum_roll_max = cum_return.cummax()
        drawdown = cum_roll_max - cum_return
        drawdown_pct = drawdown / cum_roll_max
        self.result = drawdown_pct.max()
        return self.result

    def plot(self, fig) -> go.Figure:
        pass


class Calmar(IndicatorAbstract):
    def compute(self, annual_granularity: int = AnnualGranularity.D_1.value) -> float:
        cagr = CAGR(self.data)
        cagr.compute(annual_granularity)

        mdd = MaxDrawDown(self.data)
        mdd.compute()

        self.result = round(cagr.result / mdd.result, 2)
        return self.result

    def plot(self, fig) -> go.Figure:
        pass


class RiskRewardRatio(IndicatorAbstract):
    def compute(self) -> Dict[str, float]:
        ratio_risk_reward_list = list()
        nb_trades = 0
        is_buying = False
        is_selling = False
        for candle in self.data.itertuples():
            if not is_buying and not is_selling:
                if candle.action == 1:
                    is_buying = True
                    risk = candle.action_price - candle.stop_loss
                    reward = candle.take_profit - candle.action_price
                    ratio_risk_reward_list.append(round(reward / risk, 1))
                elif candle.action == -1:
                    is_selling = True
                    risk = candle.stop_loss - candle.action_price
                    reward = candle.action_price - candle.take_profit
                    ratio_risk_reward_list.append(round(reward / risk, 1))
            elif is_buying:
                if candle.action in (0, -1):
                    is_buying = False
                    nb_trades += 1
                if candle.action == -1:
                    is_selling = True
                    risk = candle.stop_loss - candle.action_price
                    reward = candle.action_price - candle.take_profit
                    ratio_risk_reward_list.append(round(reward / risk, 1))
            elif is_selling:
                if candle.action in (0, 1):
                    is_selling = False
                    nb_trades += 1
                if candle.action == 1:
                    is_buying = True
                    risk = candle.action_price - candle.stop_loss
                    reward = candle.take_profit - candle.action_price
                    ratio_risk_reward_list.append(round(reward / risk, 1))

        ratio_risk_reward_list = ratio_risk_reward_list[:nb_trades]
        ratio_risk_reward = round(float(np.mean(ratio_risk_reward_list)), 2)
        breakeven = round(100 / (1 + ratio_risk_reward), 1)
        self.result = {
            'RiskRewardRatio': ratio_risk_reward,
            'BreakevenHitRatio': breakeven
        }

        return self.result

    def plot(self, fig) -> go.Figure:
        pass
