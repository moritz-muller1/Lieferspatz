# Lieferspatz

A Flask food-delivery web application. Customers browse nearby restaurants that
deliver to their postal code, build a cart, check out, and track orders;
restaurants manage their menu, delivery areas and opening hours, and move orders
through a `Pending → Processing → Delivered` workflow.

**Live demo:** [https://lieferspatz-n96m.onrender.com]

## Tech stack

| Layer | Choice |
|---|---|
| Web framework | Flask (application-factory + blueprints) |
| Database | PostgreSQL, accessed with `psycopg` 3 |
| Templating | Jinja2 |
| Auth | session-based, `pbkdf2:sha256` password hashing |
| Image storage | Cloudinary (optional; falls back to bundled images) |
| Hosting | Render (`gunicorn`), database on Neon |

## Project layout

```
├── render.yaml             # Render blueprint (rootDir: Code)
├── Lieferspatz-ER.jpg      # entity-relationship diagram
├── ConceptPaper.pdf        # original project brief
└── Code/
    ├── run.py              # WSGI entry point (gunicorn run:app)
    ├── config.py           # env-driven configuration
    ├── requirements.txt
    ├── Procfile · runtime.txt
    ├── .env.example        # template for local secrets
    ├── schema/
    │   ├── schema.sql      # PostgreSQL DDL
    │   └── seed.sql        # seed data (10 restaurants, 100 menu items, sample orders)
    ├── scripts/
    │   └── init_db.py      # load schema + seed into DATABASE_URL
    └── app/
        ├── __init__.py     # create_app() application factory
        ├── db.py           # per-request PostgreSQL connection on flask.g
        ├── storage.py      # Cloudinary image uploads
        ├── templates/ · static/
        └── blueprints/
            ├── main.py        # landing page
            ├── auth.py        # sign up / log in / log out
            ├── customer.py    # restaurants, menu, cart, checkout, tracking, history
            └── restaurant.py  # dashboard, menu & delivery-area management, orders
```

## Running locally

You need a PostgreSQL database. The quickest option is a free
[Neon](https://neon.tech) project — create one and copy its connection string.

```bash
cd Code
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env              # then edit .env — at minimum set DATABASE_URL
python -m scripts.init_db         # creates tables and loads seed data

python run.py                     # http://127.0.0.1:5000
```

`gunicorn` is Linux-only; on Windows use `python run.py` for local development.

### Test logins (from the seed data)

| Role | Username | Password |
|---|---|---|
| Customer | `john_doe` | `password123` |
| Restaurant | `Gourmet_Palace` | `delivery123` |

## Configuration

All configuration comes from environment variables, loaded from `Code/.env`
locally (git-ignored) and set in the host dashboard in production.

| Variable | Required | Purpose |
|---|---|---|
| `DATABASE_URL` | yes | PostgreSQL connection string |
| `SECRET_KEY` | production | Flask session signing |
| `CLOUDINARY_URL` | no | Enables restaurant image uploads (`cloudinary://key:secret@cloud`) |
| `SESSION_COOKIE_SECURE` | no | `true`/`false`; auto-on when `RENDER` is set |

### Image uploads

Restaurant sign-up accepts a picture. With `CLOUDINARY_URL` set, the image is
uploaded to Cloudinary and its URL stored on the restaurant. Without it, sign-up
still works and the app uses the bundled images in `app/static/images/`.

## Deploying to Render

1. Push the repo to GitHub.
2. Create a **Neon** database and load the schema:
   `DATABASE_URL=<neon-url> python -m scripts.init_db`
3. In Render: **New → Blueprint**, point at the repo. `render.yaml` is at the
   repository root and sets `rootDir: Code`.
4. In the service's **Environment** tab set `DATABASE_URL` (and optionally
   `CLOUDINARY_URL`); Render generates `SECRET_KEY` automatically.
5. Deploy. Render runs `gunicorn run:app`; auto-deploys on every push.

## Notes on the SQLite → PostgreSQL migration

The project originally used a local SQLite file. Moving to PostgreSQL for
deployment required:

- **Quoted identifiers** — the original PascalCase table/column names are
  case-sensitive in Postgres, so every identifier in every query is
  double-quoted.
- **Parameter style** — `?` placeholders became `%s`.
- **Inserts** — `last_insert_rowid()` became `RETURNING`.
- **String literals** — SQLite tolerates `"double quotes"` for strings; Postgres
  requires `'single quotes'`.
- **Types** — postal codes and opening hours are stored as `varchar` to preserve
  the original text-comparison behaviour.
- **Connections** — one connection per request, stored on `flask.g` and closed
  in a teardown handler, instead of a new connection per query.

The data model is unchanged from the original design ([`Lieferspatz-ER.jpg`](Lieferspatz-ER.jpg)).
Seed passwords are stored hashed.
