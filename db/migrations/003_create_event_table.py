from yoyo import step

__depends__ = {"001_init_db"}

step('''
    CREATE TABLE IF NOT EXISTS trading.event (
        id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        date TIMESTAMP NOT NULL,
        country text NOT NULL,
        importance SMALLINT NOT NULL,
        name text NOT NULL,
        actual_value NUMERIC,
        is_positive SMALLINT NOT NULL,
        forecast_value NUMERIC,
        previous_value NUMERIC,
        PRIMARY KEY (id),
        UNIQUE (date, country, name)
    );
''')