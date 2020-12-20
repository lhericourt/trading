from yoyo import step

__depends__ = {'002_create_candle_table'}

steps = [
    step('''
        CREATE INDEX idx_candle_date ON trading.candle(date);
    '''),
    step('''
        CREATE INDEX idx_candle_symbol ON trading.candle(symbol);
    '''),
    step('''
        CREATE INDEX idx_candle_date_symbol ON trading.candle(date, symbol);
''')
]
