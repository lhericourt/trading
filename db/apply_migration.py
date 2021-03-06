from pathlib import Path
from yoyo import read_migrations, get_backend

from db.utils import get_uri_db


def do_migration(schema: str = None) -> None:
    uri = get_uri_db(schema)
    backend = get_backend(uri)
    migrations = read_migrations(str(Path('db') / Path('migrations')))
    backend.apply_migrations(backend.to_apply(migrations))
    return None
