from typing import Tuple
import plotly.graph_objects as go
import numpy as np
import pandas as pd

from indicator.indicator import IndicatorAbstract
from utils.utils import compute_average


class Atr(IndicatorAbstract):
    def compute(self, span: int = 14, avg_type='ma') -> Tuple[np.ndarray, np.ndarray]:
        tr = pd.DataFrame()
        tr['HL'] = self.data['high'] - self.data['low']
        tr['HC'] = (self.data['high'] - self.data.shift(1)['close']).abs()
        tr['LC'] = (self.data['low'] - self.data.shift(1)['close']).abs()
        tr_max = tr.max(axis=1)
        self.result = (np.array(compute_average(tr_max, span, avg_type)), np.array(tr_max))
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


class Macd(IndicatorAbstract):
    def compute(self, span_fast: int = 12, span_slow: int = 26, span_signal: int = 9) -> Tuple[np.ndarray,
                                                                                               np.ndarray, np.ndarray]:
        ewm_fast = self.data[self.col].ewm(span=span_fast, min_periods=span_fast).mean()
        ewm_slow = self.data[self.col].ewm(span=span_slow, min_periods=span_slow).mean()
        macd_line = ewm_fast - ewm_slow
        signal = macd_line.ewm(span=span_signal, min_periods=span_signal).mean()
        hist = macd_line - signal
        self.result = (macd_line.values, signal.values, macd_line.values)
        return self.result

    def plot(self, fig: go.Figure) -> go.Figure:
        width = 2
        color1 = 'rgba(46, 134, 193, 0.5)'
        color2 = 'rgba(40, 180, 99, 0.5)'
        color3 = 'rgba(136, 78, 160, 0.5)'
        position = (1, 1)
        macd_, signal, hist = self.result

        #fig.add_trace(go.Scatter(x=self.data['date'],
        #                         y=macd_,
        #                         mode='lines',
        #                         name='macd',
        #                         line=dict(color=color1, width=width)
        #                         ),
        #              row=position[0], col=position[1]
        #              )
        fig.add_trace(go.Scatter(x=self.data['date'],
                                 y=signal,
                                 mode='lines',
                                 name='macd_signal',
                                 line=dict(color=color2, width=width)
                                 ),
                      row=position[0], col=position[1]
                      )
        fig.add_trace(go.Bar(x=self.data['date'],
                             y=hist,
                             marker_color=color3,
                             name='macd_hist', ),
                      row=position[0], col=position[1]
                      )

        return fig


class Rsi(IndicatorAbstract):
    def compute(self, span=14) -> np.ndarray:
        delta = self.data[self.col] - self.data[self.col].shift(1)
        delta_pos = np.where(delta >= 0, delta, 0)
        delta_neg = np.where(delta < 0, abs(delta), 0)
        avg_gain = list()
        avg_loss = list()
        for i in range(len(self.data)):
            if i < span:
                avg_gain.append(np.NaN)
                avg_loss.append(np.NaN)
            elif i == span:
                avg_gain.append(np.mean(delta_pos[:span]))
                avg_loss.append(np.mean(delta_neg[:span]))
            else:
                avg_gain.append(((span - 1) * avg_gain[-1] + delta_pos[i]) / span)
                avg_loss.append(((span - 1) * avg_loss[-1] + delta_neg[i]) / span)
        avg_gain = np.array(avg_gain)
        avg_loss = np.array(avg_loss)

        # if avg_loss is null rsi must be equal to 100
        avg_loss = np.where(avg_loss == 0, 1e-10, avg_loss)

        rs = avg_gain / avg_loss
        self.result = 100 - 100 / (1 + rs)

        return self.result

    def plot(self, fig: go.Figure) -> go.Figure:
        width = 2
        color1 = 'rgba(46, 134, 193, 0.5)'
        position = (1, 1)
        rsi = self.result

        fig.add_trace(go.Scatter(x=self.data['date'],
                                 y=rsi,
                                 mode='lines',
                                 name='rsi',
                                 line=dict(color=color1, width=width)
                                 ),
                      row=position[0], col=position[1]
                      )

        fig.add_shape(type="line",
                      x0=self.data['date'].min(), y0=30,
                      x1=self.data['date'].max(), y1=30,
                      line=dict(color=color1, width=width, dash="dot"),
                      row=position[0], col=position[1]
                      )

        fig.add_shape(type="line",
                      x0=self.data['date'].min(), y0=70,
                      x1=self.data['date'].max(), y1=70,
                      line=dict(color=color1, width=width, dash="dot"),
                      row=position[0], col=position[1]
                      )
        return fig


class Stochastic(IndicatorAbstract):
    def compute(self, span_fast=14, span_slow=3, slow=False) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        low = self.data['low'].rolling(span_fast, min_periods=span_fast).min()
        high = self.data['high'].rolling(span_fast, min_periods=span_fast).max()
        stoch = 100 * (self.data['close'] - low) / (high - low)
        stoch_ma = stoch.rolling(span_slow, min_periods=span_slow).mean()
        if slow:
            stoch = stoch_ma
            stoch_ma = stoch.rolling(span_slow, min_periods=span_slow).mean()
        stoch_hist = stoch - stoch_ma
        self.result = (stoch.values, stoch_ma.values, stoch_hist.values)
        return self.result

    def plot(self, fig: go.Figure) -> go.Figure:
        width = 2
        color1 = 'rgba(46, 134, 193, 0.5)'
        color2 = 'rgba(40, 180, 99, 0.5)'
        color3 = 'rgba(136, 78, 160, 0.5)'
        position = (1, 1)
        stoch_fast, stoch_slow, stoch_hist = self.result

        fig.add_trace(go.Scatter(x=self.data['date'],
                                 y=stoch_fast,
                                 mode='lines',
                                 name='stochastic_fast',
                                 line=dict(color=color1, width=width)
                                 ),
                      row=position[0], col=position[1]
                      )
        fig.add_trace(go.Scatter(x=self.data['date'],
                                 y=stoch_slow,
                                 mode='lines',
                                 name='stochastic_slow',
                                 line=dict(color=color2, width=width)
                                 ),
                      row=position[0], col=position[1]
                      )
        fig.add_trace(go.Bar(x=self.data['date'],
                             y=stoch_hist,
                             marker_color=color3,
                             name='stoch_hist', ),
                      row=position[0], col=position[1]
                      )
        fig.add_shape(type="line",
                      x0=self.data['date'].min(), y0=20,
                      x1=self.data['date'].max(), y1=20,
                      line=dict(color=color3, width=width, dash="dot"),
                      row=position[0], col=position[1]
                      )

        fig.add_shape(type="line",
                      x0=self.data['date'].min(), y0=80,
                      x1=self.data['date'].max(), y1=80,
                      line=dict(color=color3, width=width, dash="dot"),
                      row=position[0], col=position[1]
                      )
        return fig


class Obv(IndicatorAbstract):
    def compute(self) -> np.ndarray:
        change = self.data['close'].pct_change()
        direction_plus = np.where(change > 0, 1, 0)
        direction_minus = np.where(change < 0, -1, 0)
        direction = direction_plus + direction_minus
        direction[0] = 0
        volume_adj = self.data['tickqty'] * direction
        self.result = volume_adj.cumsum().values
        return self.result

    def plot(self, fig: go.Figure) -> go.Figure:
        width = 2
        color1 = 'rgba(46, 134, 193, 0.5)'
        position = (1, 1)
        obv = self.result

        fig.add_trace(go.Scatter(x=self.data['date'],
                                 y=obv,
                                 mode='lines',
                                 name='obv',
                                 line=dict(color=color1, width=width)
                                 ),
                      row=position[0], col=position[1]
                      )

        return fig


class AwesomeOscillator(IndicatorAbstract):
    def compute(self, span_fast: int = 5, span_slow: int = 34) -> np.ndarray:
        self.data['median'] = (self.data['high'] + self.data['low']) / 2
        sma_fast = self.data['median'].rolling(span_fast, min_periods=span_fast).mean()
        sma_slow = self.data['median'].rolling(span_slow, min_periods=span_slow).mean()
        self.result = sma_fast - sma_slow
        return self.result.values

    def plot(self, fig: go.Figure) -> go.Figure:
        color = 'rgba(136, 78, 160, 0.5)'
        position = (1, 1)
        ao = self.result
        fig.add_trace(go.Bar(x=self.data['date'],
                             y=ao,
                             marker_color=color,
                             name='awesome oscillator', ),
                      row=position[0], col=position[1]
                      )
        return fig


