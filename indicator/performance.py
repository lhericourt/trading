import plotly.graph_objects as go

from indicator.indicator import IndicatorAbstract
from utils.utils import AnnualGranularity


class CAGR(IndicatorAbstract):
    def compute(self, annual_granularity: int = AnnualGranularity.D_1.value) -> float:
        # Be careful only for daily data
        daily_return = self.data[self.col].pct_change()
        cum_return = (1 + daily_return).cumprod()
        n = len(daily_return) / annual_granularity
        self.result = (cum_return.values[-1])**(1/n) - 1
        return self.result

    def plot(self, fig) -> go.Figure:
        pass
