import plotly.graph_objects as go
import numpy as np
import pandas as pd

from indicator.indicator import IndicatorAbstract


class Macd(IndicatorAbstract):
    def compute(self, span_fast: int = 12, span_slow: int = 26, span_signal: int = 9) -> None:
        ewm_fast = self.data[self.col].ewm(span=span_fast, min_periods=span_fast).mean()
        ewm_slow = self.data[self.col].ewm(span=span_slow, min_periods=span_slow).mean()
        macd_ = ewm_fast - ewm_slow
        signal = macd_.ewm(span=span_signal, min_periods=span_signal).mean()
        hist = macd_ - signal
        self.result = (macd_, signal, hist)
        return

    def plot(self, fig: go.Figure) -> go.Figure:
        width = 2
        color1 = 'rgba(46, 134, 193, 0.5)'
        color2 = 'rgba(40, 180, 99, 0.5)'
        color3 = 'rgba(136, 78, 160, 0.5)'
        position = (1, 1)
        macd_, signal, hist = self.result

        fig.add_trace(go.Scatter(x=self.data['date'],
                                 y=macd_,
                                 mode='lines',
                                 name='macd',
                                 line=dict(color=color1, width=width)
                                 ),
                      row=position[0], col=position[1]
                      )
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
    def compute(self, span=14) -> None:
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
        rs = avg_gain / avg_loss
        self.result = 100 - 100 / (1 + rs)
        return

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
    def compute(self, span_fast=14, span_slow=3, slow=False) -> None:
        low = self.data['low'].rolling(span_fast, min_periods=span_fast).min()
        high = self.data['high'].rolling(span_fast, min_periods=span_fast).max()
        stoch = 100 * (self.data['close'] - low) / (high - low)
        stoch_ma = stoch.rolling(span_slow, min_periods=span_slow).mean()
        if slow:
            stoch = stoch_ma
            stoch_ma = stoch.rolling(span_slow, min_periods=span_slow).mean()
        stoch_hist = stoch - stoch_ma
        self.result = (stoch, stoch_ma, stoch_hist)
        return

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
