import plotly.graph_objects as go

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
