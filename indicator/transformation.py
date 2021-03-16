from typing import Tuple
import plotly.graph_objects as go
import numpy as np

from indicator.indicator import IndicatorAbstract


class Fisher(IndicatorAbstract):
    def compute(self, span: int = 55) -> Tuple[np.ndarray, np.ndarray]:
        min_col = self.data[self.col].rolling(span, min_periods=span).min()
        max_col = self.data[self.col].rolling(span, min_periods=span).max()
        normed_col = (self.data[self.col] - min_col) / (max_col - min_col)
        normed_col = 2 * normed_col - 1
        normed_col = np.where(normed_col == 1, 0.999, normed_col)
        normed_col = np.where(normed_col == -1, -0.999, normed_col)
        self.result = 0.5 * np.log((1 + normed_col) / (1 - normed_col))
        return self.result

    def plot(self, fig) -> go.Figure:
        width = 1
        color1 = 'rgba(46, 134, 193, 0.5)'
        position = (1, 1)
        atr, _ = self.result
        fig.add_trace(go.Scatter(x=self.data['date'],
                                 y=atr,
                                 mode='lines',
                                 name='atr',
                                 line=dict(color=color1, width=width)
                                 ),
                      row=position[0], col=position[1]
                      )
        return fig