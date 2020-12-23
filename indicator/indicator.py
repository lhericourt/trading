from abc import ABC, abstractmethod

from pandas import DataFrame
import plotly.graph_objects as go


class IndicatorAbstract(ABC):
    def __init__(self, data: DataFrame, col: str = None):
        self.data = data
        self.col = col
        self.result = None

    @abstractmethod
    def compute(self, **kwargs) -> None:
        pass

    @abstractmethod
    def plot(self, **kwargs) -> go.Figure:
        pass
