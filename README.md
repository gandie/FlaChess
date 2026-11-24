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

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) for the operator application
shell. The framework-free SPA includes URL-backed Overview and System views;
Tournament views list status and structure counts, create draft tournaments,
and open stable overviews where draft metadata can be edited. The Player view
creates and edits reusable player records. Draft tournament overviews register
and unregister named players; active and finished rosters are read-only. They
also configure ordered phases and sections, planned rounds, named section
membership with optional ratings, and ordered tie-break rules. Draft readiness
mirrors the backend activation blocker and separately reports missing setup
items; supported standings codes are identified and configured unsupported
codes remain visibly flagged. Tie-break-locked and non-draft sections are
read-only in the overview. Operators can activate an eligible draft tournament
from the overview, activate a section, and open its dedicated operation view.
Active sections support round creation, manual game pairings, valid score entry,
result types, comments, and byes, unplayed rounds, absences, and awarded scores.
Section operation includes URL-backed round navigation, explicit incomplete
versus recorded game states, and standings through the selected round. Result
changes recompute that round's snapshot; the table shows player names, rank,
points, wins/draws/losses, active tie-break columns, and snapshot time.
The System view runs a database-independent health check and demonstrates
normalized API error handling.

The API is available at
[http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health) for the
API health response, or [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
for the interactive API documentation. The app checks PostgreSQL during
startup; if `DATABASE_URL` is unset or the database cannot be reached, it logs
a warning and continues to serve routes that do not use the database.

With `DATABASE_URL` configured, CRUD is available under `/api/players`,
`/api/tournaments`, and `/api/tournament-participants`. Tournaments start in
`draft`; use `POST /api/tournaments/{id}/activate` after registering at least
two participants, then `POST /api/tournaments/{id}/finish`. Other lifecycle
transitions return a `409` response. The operator catalog uses
`GET /api/tournament-summaries`, which returns lifecycle and participant,
phase, and section counts without a paginated CRUD envelope. Operator player
contracts are `GET /api/player-summaries` and the scoped
`/api/tournaments/{id}/participants` read, create, and delete routes. Participant
writes reject tournaments outside the `draft` lifecycle. The direct
`GET /api/tournaments/{id}/workspace` contract supplies named participants,
nested phases and sections, section memberships and ratings, ordered tie-break
configuration, supported codes, and activation readiness in one response.
`GET /api/tournament-sections/{id}/operation` supplies named section members,
ordered rounds, games, round participation records, and active ordered
tie-break metadata for the operator view. Standing snapshots are read from
`GET /api/tournament-sections/{id}/standings?through_round_id={round_id}` and
recomputed through
`POST /api/tournament-sections/{id}/standings/recompute?through_round_id={round_id}`.
Lifecycle actions remain `POST /api/tournaments/{id}/activate` and
`POST /api/tournament-sections/{id}/activate`, with authoritative `409`
conflicts for invalid transitions.

The SQLAdmin interface is mounted at
[http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin) and provides list,
detail, create, edit, search, and delete forms for Player, Tournament, and
Tournament Participant records. SQLAdmin lifecycle edits are excluded so
transitions remain route-controlled. SQLAdmin is currently not protected by
application authentication or authorization.

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

## Database development

Run SQL against the PostgreSQL service from the repository root with the
PowerShell helper. The service must already be running with `docker compose up`.
For example:

```powershell
.\tools\psql.ps1 -Query "SELECT id, name FROM player;"
```

The helper uses the local `.env.example` values (`fla_chess` for both
`POSTGRES_USER` and `POSTGRES_DB`); update its `-U`/`-d` values if those
development settings change. It stops on SQL errors and passes the query as a
single argument to `psql`'s `-c` option.

## Database migrations

The project has an async Alembic environment configured to use `DATABASE_URL`
and the app's declarative metadata. Migrations create `player`, `tournament`,
and `tournament_participant`. From a running Compose stack, apply migrations
with:

```powershell
docker compose exec app alembic upgrade head
```

Generate future migrations after adding models, for example:

```powershell
docker compose exec app alembic revision --autogenerate -m "add tournament model"
```

For Alembic commands run on the host, `DATABASE_URL` must use `127.0.0.1`;
the `postgres` hostname from the Compose `.env` is only resolvable inside the
Compose network.