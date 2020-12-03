from yoyo import step

__depends__ = {}

steps = [
    step('''
        CREATE SCHEMA IF NOT EXISTS trading AUTHORIZATION admin;
    '''),
    step('''
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    ''')
]
