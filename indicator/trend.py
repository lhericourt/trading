import plotly.graph_objects as go
import pandas as pd
import numpy as np

from indicator.indicator import IndicatorAbstract


class BollingerBands(IndicatorAbstract):
    def compute(self, span: int = 20, nb_std: int = 2) -> None:
        ma = self.data[self.col].rolling(span, min_periods=span).mean()
        bb_up = ma + nb_std * self.data[self.col].rolling(span, min_periods=span).std()
        bb_down = ma - nb_std * self.data[self.col].rolling(span, min_periods=span).std()
        self.result = (ma, bb_up, bb_down)
        return

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
    def compute(self, span=14) -> None:
        # compute true range
        tr = pd.DataFrame()
        tr['HL'] = self.data['high'] - self.data['low']
        tr['HC'] = (self.data['high'] - self.data.shift(1)['close']).abs()
        tr['LC'] = (self.data['low'] - self.data.shift(1)['close']).abs()
        tr_max = np.array(tr.max(axis=1))

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

        self.result = [dm_plus_norm, dm_minus_norm, np.array(adx)]
        return

    def plot(self, fig) -> go.Figure:
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
