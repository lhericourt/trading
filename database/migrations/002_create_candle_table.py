from yoyo import step

__depends__ = {"001_init_db"}

step('''
    CREATE TABLE IF NOT EXISTS trading.candle (
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
''')