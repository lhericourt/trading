from plotly.subplots import make_subplots
import plotly.graph_objects as go
import pandas as pd


def filter_data(candles, table, symbol=None, start_date=None, end_date=None):
    mask = (candles['table'] == table)
    if symbol:
        mask = mask & (candles['symbol'] == symbol)
    if start_date and end_date:
        mask = mask & (candles['date'] >= start_date) & (candles['date'] < end_date)
    candles_to_show = candles[mask]
    return candles_to_show


def show_candle(candles, size=(1400, 800)):
    layout = go.Layout(
        autosize=True,
        width=size[0],
        height=size[1],
        xaxis=go.layout.XAxis(linecolor='black',
                              linewidth=1,
                              mirror=True),
        xaxis2=go.layout.XAxis(linecolor='black',
                               linewidth=1,
                               mirror=True),
        yaxis=go.layout.YAxis(linecolor='black',
                              linewidth=1,
                              mirror=True,
                              domain=[0, 0.2]),
        yaxis2=go.layout.YAxis(linecolor='black',
                               linewidth=1,
                               mirror=True,
                               domain=[0.3, 1]),

    )

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True)
    fig.update_layout(layout, xaxis2_rangeslider_visible=False)
    fig.add_trace(go.Candlestick(x=candles['date'],
                                 open=candles['open'],
                                 high=candles['high'],
                                 low=candles['low'],
                                 close=candles['close']),
                  row=2, col=1)

    fig.update_yaxes(fixedrange=False)
    # fig.update_xaxes(rangebreaks=[dict(values=compute_datetime_to_hide(start_date, end_date))])

    return fig


def add_indicator(data: pd.DataFrame, fig: go.Figure, name: str, color: str = 'rgba(46, 134, 193, 0.5)') -> go.Figure:
    width = 2
    fig.add_trace(go.Scatter(x=data['date'],
                             y=data[name],
                             mode='lines',
                             name=name,
                             line=dict(color=color, width=width)
                             ),
                  row=2, col=1
                  )
    return fig
