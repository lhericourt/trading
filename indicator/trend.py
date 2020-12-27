from typing import Tuple
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

from indicator.indicator import IndicatorAbstract
from indicator.oscillator import Atr


class BollingerBands(IndicatorAbstract):
    def compute(self, span: int = 20, nb_std: int = 2) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        ma = self.data[self.col].rolling(span, min_periods=span).mean()
        bb_up = ma + nb_std * self.data[self.col].rolling(span, min_periods=span).std()
        bb_down = ma - nb_std * self.data[self.col].rolling(span, min_periods=span).std()
        self.result = (ma.values, bb_up.values, bb_down.values)
        return self.result

    def plot(self, fig: go.Figure) -> go.Figure:
        width = 2
        color = 'rgba(46, 134, 193, 0.5)'
        ma, bb_up, bb_down = self.result

        fig.add_trace(go.Scatter(x=self.data['date'],
                                 y=bb_up,
                                 mode='lines',
                                 name='bollinger_up',
                                 line=dict(color=color, width=width)
                                 ),
                      row=2, col=1
                      )
        fig.add_trace(go.Scatter(x=self.data['date'],
                                 y=bb_down,
                                 mode='lines',
                                 name='bollinger',
                                 line=dict(color=color, width=width)

                                 ),
                      row=2, col=1
                      )
        fig.add_trace(go.Scatter(x=self.data['date'],
                                 y=ma,
                                 mode='lines',
                                 name='bollinger_dow',
                                 line=dict(color=color, width=width)

                                 ),
                      row=2, col=1
                      )

        return fig


class Adx(IndicatorAbstract):
    def compute(self, span=14) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        # compute true range
        atr = Atr(self.data, self.col)
        atr.compute(span)
        _, tr_max = atr.result

        # compute positive directional movement
        dm_plus = np.where((self.data['high'] - self.data.shift(1)['high']) > (self.data.shift(1)['low'] - self.data['low']),
                           self.data['high'] - self.data.shift(1)['high'], 0)
        dm_plus = np.where(dm_plus > 0, dm_plus, 0)

        # compute negative directional movement
        dm_minus = np.where((self.data.shift(1)['low'] - self.data['low']) > (self.data['high'] - self.data.shift(1)['high']),
                            self.data.shift(1)['low'] - self.data['low'], 0)
        dm_minus = np.where(dm_minus > 0, dm_minus, 0)

        # compute smoothed values
        tr_max_n = list()
        dm_plus_n = list()
        dm_minus_n = list()
        for i in range(len(self.data)):
            if i < span:
                tr_max_n.append(np.NaN)
                dm_plus_n.append(np.NaN)
                dm_minus_n.append(np.NaN)
            elif i == span:
                tr_max_n.append(np.sum(tr_max[1: span + 1]))
                dm_plus_n.append(np.sum(dm_plus[1: span + 1]))
                dm_minus_n.append(np.sum(dm_minus[1: span + 1]))
            else:
                tr_max_n.append(tr_max_n[-1] - (tr_max_n[-1] / span) + tr_max[i])
                dm_plus_n.append(dm_plus_n[-1] - (dm_plus_n[-1] / span) + dm_plus[i])
                dm_minus_n.append(dm_minus_n[-1] - (dm_minus_n[-1] / span) + dm_minus[i])
        tr_max_n = np.array(tr_max_n)
        dm_plus_n = np.array(dm_plus_n)
        dm_minus_n = np.array(dm_minus_n)

        # normalisation
        dm_plus_norm = 100 * dm_plus_n / tr_max_n
        dm_minus_norm = 100 * dm_minus_n / tr_max_n

        # compute average directional index
        dx = 100 * (np.abs(dm_plus_norm - dm_minus_norm)) / (dm_plus_norm + dm_minus_norm)

        adx = list()
        for i in range(len(self.data)):
            if i < 2 * span - 1:
                adx.append(np.NaN)
            elif i == 2 * span - 1:
                adx.append(np.mean(dx[span: 2 * span]))
            else:
                adx.append(((span - 1) * adx[-1] + dx[i]) / span)

        self.result = (dm_plus_norm, dm_minus_norm, np.array(adx))
        return self.result

    def plot(self, fig: go.Figure) -> go.Figure:
        color1 = 'rgba(46, 134, 193, 0.5)'
        color2 = 'rgba(40, 180, 99, 0.5)'
        color3 = 'rgba(136, 78, 160, 0.5)'
        dmi_plus = self.result[0]
        dmi_minus = self.result[1]
        adx = self.result[2]

        fig.add_trace(go.Scatter(x=self.data['date'],
                                 y=adx,
                                 mode='lines',
                                 name='adx',
                                 line=dict(color=color1, width=2)
                                 ),
                      row=1, col=1
                      )
        fig.add_trace(go.Scatter(x=self.data['date'],
                                 y=dmi_plus,
                                 mode='lines',
                                 name='dmi_pos',
                                 line=dict(color=color2, width=1)
                                 ),
                      row=1, col=1
                      )
        fig.add_trace(go.Scatter(x=self.data['date'],
                                 y=dmi_minus,
                                 mode='lines',
                                 name='dmi_neg',
                                 line=dict(color=color3, width=1)
                                 ),
                      row=1, col=1
                      )

        return fig


class Slope(IndicatorAbstract):
    def compute(self, span: int = 5) -> np.ndarray:
        data = self.data[self.col].reset_index(drop=True)
        slopes = [0] * (span - 1)
        for i in range(span, len(data) + 1):
            y = data[i-span:i]
            x = np.arange(span).reshape((span, 1))
            y_scaled = (y - y.min()) / (y.max() - y.min())
            x_scaled = (x - x.min()) / (x.max() - x.min())
            lr = LinearRegression()
            lr.fit(x_scaled, y_scaled)
            slopes.append(lr.coef_[0])

        self.result = np.rad2deg(np.arctan(np.array(slopes)))
        return self.result

    def plot(self, fig: go.Figure) -> go.Figure:
        width = 2
        color = 'rgb(46, 134, 193)'
        slope = self.result

        fig.add_trace(go.Scatter(x=self.data['date'],
                                 y=slope,
                                 mode='lines',
                                 name='slope',
                                 line=dict(color=color, width=width)
                                 ),
                      row=1, col=1
                      )
        return fig


class Renko(IndicatorAbstract):
    def compute(self, box_size: float = 1e-3) -> Tuple[np.ndarray, np.ndarray]:
        data = self.data[self.col].tolist()
        dates = self.data['date'].tolist()
        renko = list()
        renko_dates = list()
        renko.append(int(data[0]))
        renko_dates.append(dates[0])
        cum_sum = 0
        for i in range(1, len(data)):
            cum_sum += (data[i] - data[i-1])
            if abs(cum_sum) >= box_size:
                renko_val = renko[-1] + 1 if cum_sum > 0 else renko[-1] - 1
                renko.append(renko_val)
                renko_dates.append(dates[i])
                cum_sum = 0
        self.result = (np.array(renko), np.array(renko_dates))
        return self.result

    def plot(self, fig: go.Figure) -> go.Figure:
        size = 3
        color = 'rgb(46, 134, 193)'
        renko, renko_dates = self.result

        fig.add_trace(go.Scatter(x=renko_dates,
                                 y=renko,
                                 mode='markers',
                                 name='renko',
                                 marker=dict(color=color, size=size)
                                 ),
                      row=1, col=1
                      )
        return fig