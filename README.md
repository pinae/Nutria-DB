# Nutria-DB
Food database.

Runs on Django 6.0, Python 3.12+ and PostgreSQL. Dependencies are managed
with [uv](https://docs.astral.sh/uv/).

## Development setup

Clone this repository, enter the folder and install the dependencies:

```
cd Nutria-DB
uv sync
```

`uv sync` creates a virtual environment in `.venv` and installs the locked
dependency versions from `uv.lock`. Development uses a local SQLite database
by default, so no database server is needed.

Set up the database:

```
cd nutriaDB
uv run manage.py migrate
uv run manage.py createsuperuser
uv run manage.py initial_data
```

The last command populates your database with food data from the fixtures in
the repository.

Run the development server with:

```
uv run manage.py runserver
```

Run the test suite with:

```
uv run manage.py test
```

## Using PostgreSQL

Point the application at a PostgreSQL server through environment variables:

```
export NUTRIA_DB_ENGINE=django.db.backends.postgresql
export NUTRIA_DB_NAME=nutria
export NUTRIA_DB_USER=nutria
export NUTRIA_DB_PASSWORD=...
export NUTRIA_DB_HOST=localhost
export NUTRIA_DB_PORT=5432
```

The PostgreSQL driver (psycopg 3) is installed as a regular dependency, no
extra system packages are required.

## Production with Docker

`docker-compose.yml` starts three containers: PostgreSQL 17, the Django
application served by gunicorn, and nginx as a reverse proxy that also
serves the static files.

Before the first start, replace every `change-me-...` value in
`docker-compose.yml` with your own secrets and add your domain to
`NUTRIA_ALLOWED_HOSTS`. Then:

```
docker compose up --build
```

The application initializes itself on startup (waits for the database,
applies migrations, collects static files, creates the admin account and
loads the fixture data) and is reachable on `127.0.0.1:8504`.

## Migrating data from an existing MariaDB installation

The fixture format is database agnostic, so the old database can be exported
and imported with Django's built-in commands. With the old MariaDB-based
version still configured:

```
uv run manage.py dumpdata --natural-foreign --natural-primary \
    -e contenttypes -e auth.Permission -e sessions -o nutria-dump.json
```

Then, configured against the new PostgreSQL database:

```
uv run manage.py migrate
uv run manage.py loaddata nutria-dump.json
```
