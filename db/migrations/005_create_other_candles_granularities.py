from yoyo import step

__depends__ = {'001_init_db'}

steps = [
    step('''
        CREATE TABLE IF NOT EXISTS trading.candle15m (
            id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            date TIMESTAMP NOT NULL,
            symbol text NOT NULL,
            open NUMERIC NOT NULL,
            close NUMERIC NOT NULL,
            low NUMERIC NOT NULL,
            high NUMERIC NOT NULL,
            PRIMARY KEY (id),
            UNIQUE (date, symbol)
        );
    '''),
    step('''
        CREATE INDEX idx_candle15m_date ON trading.candle15m(date);
    '''),
    step('''
        CREATE INDEX idx_candle15m_symbol ON trading.candle15m(symbol);
    '''),
    step('''
        CREATE INDEX idx_candle15m_date_symbol ON trading.candle15m(date, symbol);
    '''),
    step('''
    CREATE TABLE IF NOT EXISTS trading.candle30m (
        id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        date TIMESTAMP NOT NULL,
        symbol text NOT NULL,
        open NUMERIC NOT NULL,
        close NUMERIC NOT NULL,
        low NUMERIC NOT NULL,
        high NUMERIC NOT NULL,
        PRIMARY KEY (id),
        UNIQUE (date, symbol)
    );
    '''),
    step('''
    CREATE INDEX idx_candle30m_date ON trading.candle30m(date);
    '''),
    step('''
    CREATE INDEX idx_candle30m_symbol ON trading.candle30m(symbol);
    '''),
    step('''
    CREATE INDEX idx_candle30m_date_symbol ON trading.candle30m(date, symbol);
    '''),

    step('''
    CREATE TABLE IF NOT EXISTS trading.candle1h (
        id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        date TIMESTAMP NOT NULL,
        symbol text NOT NULL,
        open NUMERIC NOT NULL,
        close NUMERIC NOT NULL,
        low NUMERIC NOT NULL,
        high NUMERIC NOT NULL,
        PRIMARY KEY (id),
        UNIQUE (date, symbol)
    );
    '''),
    step('''
    CREATE INDEX idx_candle1h_date ON trading.candle1h(date);
    '''),
    step('''
    CREATE INDEX idx_candle1h_symbol ON trading.candle1h(symbol);
    '''),
    step('''
    CREATE INDEX idx_candle1h_date_symbol ON trading.candle1h(date, symbol);
    '''),
    step('''
    CREATE TABLE IF NOT EXISTS trading.candle4h (
        id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        date TIMESTAMP NOT NULL,
        symbol text NOT NULL,
        open NUMERIC NOT NULL,
        close NUMERIC NOT NULL,
        low NUMERIC NOT NULL,
        high NUMERIC NOT NULL,
        PRIMARY KEY (id),
        UNIQUE (date, symbol)
    );
    '''),
    step('''
    CREATE INDEX idx_candle4h_date ON trading.candle4h(date);
    '''),
    step('''
    CREATE INDEX idx_candle4h_symbol ON trading.candle4h(symbol);
    '''),
    step('''
    CREATE INDEX idx_candle4h_date_symbol ON trading.candle4h(date, symbol);
    '''),
    step('''
    CREATE TABLE IF NOT EXISTS trading.candle1d (
        id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        date TIMESTAMP NOT NULL,
        symbol text NOT NULL,
        open NUMERIC NOT NULL,
        close NUMERIC NOT NULL,
        low NUMERIC NOT NULL,
        high NUMERIC NOT NULL,
        PRIMARY KEY (id),
        UNIQUE (date, symbol)
    );
    '''),
    step('''
    CREATE INDEX idx_candle1d_date ON trading.candle1d(date);
    '''),
    step('''
    CREATE INDEX idx_candle1d_symbol ON trading.candle1d(symbol);
    '''),
    step('''
    CREATE INDEX idx_candle1d_date_symbol ON trading.candle1d(date, symbol);
''')
]
