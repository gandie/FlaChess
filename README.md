# Fla Chess

## Run locally

Install the project and its FastAPI, database, and migration dependencies into
the existing virtual environment:

```powershell
.\venv\Scripts\python.exe -m pip install -e .
```

FastAPI and Alembic load the project-root `.env` automatically. Values already
set in the shell or container take precedence. The example URL uses the Compose
hostname `postgres`; host-run commands should use `127.0.0.1` instead.

Start the development server from the repository root:

```powershell
# `.env` is loaded automatically; the host needs localhost rather than postgres.
$env:DATABASE_URL = "postgresql+asyncpg://fla_chess:fla_chess@127.0.0.1:5432/fla_chess"
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) for the hello-world page,
[http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health) for the
API health response, or [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
for the interactive API documentation. The app checks PostgreSQL during
startup; if `DATABASE_URL` is unset or the database cannot be reached, it logs
a warning and continues to serve routes that do not use the database.

## Run with Docker

Copy the example environment file, then start the FastAPI application and
PostgreSQL from the repository root:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

The application is available on
[http://127.0.0.1:8000](http://127.0.0.1:8000). PostgreSQL is published on port
`5432`. Compose reads `DATABASE_URL` and PostgreSQL's initialization settings
from `.env`; `.env` is ignored by Git. The checked-in `.env.example` uses
development-only credentials. Keep the values in `DATABASE_URL` consistent
with `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD`. Use a URL-encoded
password if it contains characters reserved in a URL.

When running the app on the host, use `127.0.0.1` in `DATABASE_URL`; the
`postgres` hostname in `.env.example` is for the app container.

## Database migrations

The project has an async Alembic environment configured to use
`DATABASE_URL` and the app's declarative metadata. No models or migration
revisions exist yet. Generate migrations after adding models, for example:

```powershell
.\venv\Scripts\alembic.exe revision --autogenerate -m "add player model"
```

For Alembic commands run on the host, `DATABASE_URL` must use `127.0.0.1`;
the `postgres` hostname from the Compose `.env` is only resolvable inside the
Compose network. From a running Compose stack, use the app container instead:

```powershell
docker compose exec app alembic revision --autogenerate -m "add player model"
```