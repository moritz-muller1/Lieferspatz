"""PostgreSQL access — one connection per request, on flask.g.

The connection is committed and closed when the request ends (rolled back if the
view raised). Views may call ``conn.commit()`` / ``conn.rollback()`` but not
``conn.close()``.
"""
import psycopg
from flask import current_app, g
from psycopg.rows import dict_row

# Lets blueprints catch DB errors without importing psycopg.
DBError = psycopg.Error


def get_db_connection():
    conn = g.get('_db')
    if conn is None or conn.closed:
        dsn = current_app.config['DATABASE_URL']
        if not dsn:
            raise RuntimeError(
                'DATABASE_URL is not set. Copy .env.example to .env and fill it in.'
            )
        conn = g._db = psycopg.connect(dsn, row_factory=dict_row)
    return conn


def close_db(exc=None):
    conn = g.pop('_db', None)
    if conn is None or conn.closed:
        return
    try:
        conn.commit() if exc is None else conn.rollback()
    except psycopg.Error:
        conn.rollback()
    finally:
        conn.close()


def init_app(app):
    app.teardown_appcontext(close_db)
