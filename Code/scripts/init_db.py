"""Create the schema and load seed data into the database in DATABASE_URL.

Usage:
    python -m scripts.init_db            # schema + seed
    python -m scripts.init_db --schema   # schema only
"""
import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / 'schema' / 'schema.sql'
SEED = ROOT / 'schema' / 'seed.sql'


def main():
    dsn = os.environ.get('DATABASE_URL')
    if not dsn:
        sys.exit('DATABASE_URL is not set (put it in .env).')

    steps = [SCHEMA]
    if '--schema' not in sys.argv:
        steps.append(SEED)

    with psycopg.connect(dsn) as conn:
        for path in steps:
            print(f'Running {path.relative_to(ROOT)} ...')
            sql = path.read_text(encoding='utf-8')
            # psycopg owns the transaction here; drop the files' own BEGIN/COMMIT.
            lines = [ln for ln in sql.splitlines()
                     if ln.strip().upper() not in ('BEGIN;', 'COMMIT;')]
            conn.execute('\n'.join(lines))
        conn.commit()
    print('Done.')


if __name__ == '__main__':
    main()
