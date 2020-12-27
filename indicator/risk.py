import plotly.graph_objects as go
import numpy as np

from indicator.indicator import IndicatorAbstract
from indicator.performance import CAGR
from utils.utils import AnnualGranularity


class Volatility(IndicatorAbstract):
    def compute(self, annual_granularity: int = AnnualGranularity.D_1.value) -> float:
        daily_return = self.data[self.col].pct_change()
        self.result = daily_return.std() * np.sqrt(annual_granularity)
        return self.result

    def plot(self, fig) -> go.Figure:
        pass


class SharpeRatio(IndicatorAbstract):
    def compute(self,annual_granularity: int = AnnualGranularity.D_1.value,  risk_free_cagr: float = 0.005) -> float:
        cagr = CAGR(self.data, self.col)
        cagr.compute(annual_granularity)

        vol = Volatility(self.data, self.col)
        vol.compute(annual_granularity)
        self.result = (cagr.result - risk_free_cagr) / vol.result
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

        self.result = cagr.result / mdd.result
        return self.result

    def plot(self, fig) -> go.Figure:
        pass
