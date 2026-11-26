# Getting started

This guide covers local setup, running the application, database development,
and the main operator and API surfaces. For a visual project overview, return
to the [README](../README.md).

## Run with Docker

Copy the example environment file, then start FastAPI and PostgreSQL from the
repository root:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Open:

- [Application](http://127.0.0.1:8000)
- [API health](http://127.0.0.1:8000/api/health)
- [Interactive API documentation](http://127.0.0.1:8000/docs)
- [SQLAdmin](http://127.0.0.1:8000/admin)

PostgreSQL is published on port `5432`. Compose reads `DATABASE_URL` and the
PostgreSQL initialization settings from `.env`, which is ignored by Git. The
checked-in `.env.example` uses development-only credentials.

Keep `DATABASE_URL` consistent with `POSTGRES_DB`, `POSTGRES_USER`, and
`POSTGRES_PASSWORD`. URL-encode a password that contains characters reserved
in a URL.

## Run on the host

Install the project and its FastAPI, database, and migration dependencies into
the existing virtual environment:

```powershell
.\venv\Scripts\python.exe -m pip install -e .
```

FastAPI and Alembic automatically load the project-root `.env`. Values already
set in the shell or container take precedence. For host-run commands, use
`127.0.0.1` instead of the Compose hostname `postgres`:

```powershell
$env:DATABASE_URL = "postgresql+asyncpg://fla_chess:fla_chess@127.0.0.1:5432/fla_chess"
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

The application checks PostgreSQL during startup. If `DATABASE_URL` is unset or
the database cannot be reached, it logs a warning and continues to serve
routes that do not use the database.

## First tournament

1. Open the tournament catalog.
2. Create a draft tournament and add reusable player records.
3. Register at least two participants and define phases, sections, rounds, and
   tie-breaks.
4. Activate the tournament, then activate an eligible section.
5. Preview and confirm pairings, or create a round manually.
6. Record results and review the recomputed standings.
7. Finish each section and then the tournament to preserve the final tables.

The setup view keeps player lists, seed suggestions, activation readiness, and
unsupported tie-break codes visible. Active and finished rosters are read-only.

### Operator workspace

- The tournament desk opens on the newest active or draft tournament.
- URL-backed views retain the current screen across refresh and browser
  navigation.
- Tournament setup preserves scroll position, open disclosures, unrelated form
  values, and keyboard focus during repeated roster actions.
- Draft section rosters collapse behind an assigned-player count.
- Player records can include a PNG, JPEG, or WebP avatar up to 5 MB. The
  server center-crops it to 200×200, converts it to PNG, and stores the
  resulting Base64 data URI with the player.
- Active operation places the current round, incomplete results, and standings
  ahead of less common controls.
- Pairing preview shows named players, colors, byes, awarded scores, warnings,
  seed order, target round, and format policy.
- Confirming a plan reloads and revalidates the expected round before creating
  it transactionally.
- Finished tournament views switch to read-only history and preserved podiums.

### Player display

Open a tournament display at:

```text
/#/display/tournaments/{id}
```

It shows the current phase, the latest round's pairings and results, round
participation notes, and standings by default. Earlier rounds remain available.
Finished tournaments use a victory-ceremony view backed by final snapshots.
Player names are paired with avatars in rosters, games, standings, podiums, and
the final ceremony; initials are used when no avatar has been uploaded.

## API routes

With `DATABASE_URL` configured, CRUD is available under:

- `/api/players`
- `/api/tournaments`
- `/api/tournament-participants`

### Tournament lifecycle

Tournaments start in `draft`. Register at least two participants, then use:

- `POST /api/tournaments/{id}/activate`
- `POST /api/tournaments/{id}/finish`
- `POST /api/tournament-sections/{id}/activate`
- `POST /api/tournament-sections/{id}/finish`

Invalid lifecycle transitions return `409`.

### Operator read and write contracts

- `GET /api/tournament-summaries` returns lifecycle and participant, phase, and
  section counts without a paginated CRUD envelope.
- `GET /api/player-summaries` supplies operator player records.
- `/api/tournaments/{id}/participants` supports scoped participant reads,
  creation, and deletion. Writes reject non-draft tournaments.
- `GET /api/tournaments/{id}/workspace` returns participants, nested phases and
  sections, section memberships and ratings, tie-break configuration, supported
  codes, activation readiness, and advancement metadata.
- `GET /api/tournament-sections/{id}/operation` returns members, rounds, games,
  participation, lifecycle state, and active tie-break metadata.
- `GET /api/tournament-sections/{id}/pairing/preview` plans the next round.
- `POST /api/tournament-sections/{id}/pairing/confirm` commits the returned
  `expected_round_number` transactionally. A `409` means the plan became stale
  or could not be committed; no partial round is retained.
- `GET /api/tournament-sections/{id}/standings?through_round_id={round_id}`
  reads standings snapshots.
- `POST /api/tournament-sections/{id}/standings/recompute?through_round_id={round_id}`
  recomputes the selected round's snapshot.

Manual round, pairing, and participation APIs remain available as recovery
controls without bypassing the standard operation view.

## SQLAdmin

SQLAdmin is mounted at `/admin` and provides list, detail, create, edit, search,
and delete forms for Player, Tournament, and Tournament Participant records.
Lifecycle edits are excluded so transitions remain route-controlled.

SQLAdmin is currently unauthenticated. It is intended for a physically
protected, single-operator deployment.

## Database development

Run SQL against the PostgreSQL service with the PowerShell helper. The service
must already be running through `docker compose up`.

```powershell
.\tools\psql.ps1 -Query "SELECT id, name FROM player;"
```

The helper also accepts a SQL file:

```powershell
# Add 24 randomized player names and three draft tournaments.
.\tools\psql.ps1 -File .\tools\seed_database.sql

# Remove tournament and player data, including dependent rows and identities.
.\tools\psql.ps1 -File .\tools\cleanup_database.sql
```

Run cleanup before reseeding when a completely fresh dataset is required.
Cleanup uses `TRUNCATE ... RESTART IDENTITY CASCADE`, removing all
tournament-owned records through database foreign keys and resetting generated
IDs.

The helper uses the `.env.example` development values (`fla_chess` for
`POSTGRES_USER` and `POSTGRES_DB`). Update its `-U` and `-d` values when those
settings change. It stops on SQL errors and passes an inline query as one
argument to `psql -c`, or streams a selected SQL file through standard input.

## Database migrations

Fla Chess uses an async Alembic environment configured through `DATABASE_URL`
and the application's declarative metadata.

From a running Compose stack:

```powershell
docker compose exec app alembic upgrade head
```

Generate a migration after changing models:

```powershell
docker compose exec app alembic revision --autogenerate -m "add tournament model"
```

For host-run Alembic commands, set `DATABASE_URL` to use `127.0.0.1`. The
`postgres` hostname in `.env.example` is only resolvable inside the Compose
network.

## Tests

Run the full Python suite from the repository root:

```powershell
.\venv\Scripts\python.exe -m unittest discover .\tests\
```

Related implementation notes live in [Design](DESIGN.md), [Data](DATA.md),
[Automation](AUTOMATION.md), and [Tie-breaks](TIE_BREAKS.md).
