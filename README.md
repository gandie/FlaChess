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
shell. The tournament-desk SPA opens on a live command view that points directly
to the newest active or draft tournament, its player display, the catalog, and
the player registry. The visual system uses compact score-sheet panels, a
sticky live-round rail, and high-contrast action states to keep tournament
operation fast without hiding less common controls. The framework-free SPA
includes URL-backed Overview and System views;
Tournament views list status and structure counts, create draft tournaments,
and open compact overviews where draft metadata can be edited. The Player view
creates and edits reusable player records. Draft tournament overviews register
and unregister named players directly from the complete player list; active
and finished rosters are read-only. They
also configure ordered phases and sections, planned rounds, named section
membership with optional ratings, and ordered tie-break rules. Section
membership uses the same player-list action pattern and defaults each new
assignment to the next seed position. Generated seed suggestions advance on
refresh, while an explicitly edited suggestion remains in place. Draft readiness
mirrors the backend activation blocker and separately reports missing setup
items; supported standings codes are identified and configured unsupported
codes remain visibly flagged. Draft section rosters and player assignment
lists are collapsed by default behind a disclosure showing the assigned-player
count. Tie-break-locked and non-draft sections are read-only in the overview
except that draft section membership can still be managed during an active
tournament for manual advancement. Membership records
may carry a prior section and source rank. Operators can activate an eligible
draft tournament from the overview, activate a section, and open its dedicated
operation view. Tournament setup refreshes retain scroll position, open
disclosures, unrelated form values, and keyboard focus so repeated roster and
structure actions do not restart the page at the top. The active round is
placed before standings, with direct
incomplete-result shortcuts, sticky round navigation, compact collapsed
pairing/participation creation controls, and save-to-next-result focus.
Active sections support round creation, manual game pairings, valid score entry,
result types, comments, and byes, unplayed rounds, absences, and awarded scores.
They can also preview the next Swiss, round-robin, or knockout round without
writing data. The preview shows named pairings, colors, byes, awarded scores,
warnings, seed order, target round, and format policy labels. A separate
confirmation action reloads and revalidates the expected round before
transactionally creating it; stale or conflicting confirmations preserve the
review and surface an actionable error. The confirmed round opens in the
existing operation view, focuses result entry, and recomputes standings after
results are saved. Previewing the following round stays disabled until the
latest round is complete. Manual round, pairing, and participation controls
remain available throughout as a fallback.
Section operation includes URL-backed round navigation, explicit incomplete
versus recorded game states, and standings through the selected round. Result
changes recompute that round's snapshot; the table shows player names, rank,
points, wins/draws/losses, active tie-break columns, and snapshot time.
Confirmed section and tournament finish actions retain final section standings
and switch tournament history to a read-only presentation.
Every tournament can also be opened through the player display link. The URL
`/#/display/tournaments/{id}` presents the current phase, that phase's latest
round pairings and results by default, with controls to revisit every earlier
round's games, participation notes, and corresponding standings. Finished
tournaments switch to a victory-ceremony presentation with a final state banner,
section champions, and podiums backed by the preserved final snapshots. The view
remains read-only, uses the existing read contracts, and includes a manual refresh
action for a shared tournament screen.
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
configuration, supported codes, activation readiness, and advancement source
section/rank metadata in one response.
`GET /api/tournament-sections/{id}/operation` supplies named section members,
ordered rounds, games, round participation records, tournament lifecycle, and
active ordered tie-break metadata for the operator and player display views.
Pairing plans are read through
`GET /api/tournament-sections/{id}/pairing/preview` and committed with
`POST /api/tournament-sections/{id}/pairing/confirm` using the returned target
round as `expected_round_number`. A `409` response means the plan became stale
or could not be committed; no partial generated round is retained. Manual
round and result APIs continue to provide recovery without bypassing the
standard operation view.
Finished tournaments remain read-only when their section operation URLs are
revisited. Standing
snapshots are read from
`GET /api/tournament-sections/{id}/standings?through_round_id={round_id}` and
recomputed through
`POST /api/tournament-sections/{id}/standings/recompute?through_round_id={round_id}`.
Lifecycle actions remain `POST /api/tournaments/{id}/activate`,
`POST /api/tournaments/{id}/finish`,
`POST /api/tournament-sections/{id}/activate`, and
`POST /api/tournament-sections/{id}/finish`, with authoritative `409` conflicts
for invalid transitions.

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