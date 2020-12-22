import plotly.graph_objects as go

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
        width = 1
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