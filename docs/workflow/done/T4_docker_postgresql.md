---
agent_evaluation:
  version: 1
  evaluator: human_operator
  evaluated_at: YYYY-MM-DD
  verdict: accepted
  would_delegate_similar_again: true

  score_scale:
    min: 1
    max: 5
    meaning:
      1: poor
      3: acceptable
      5: excellent

  outcome:
    correctness:
    scope_discipline:
    validation_trust:

  collaboration:
    ambiguity_handling:
    operator_load:
    trust_delta:

  notes: >
    HUMAN NOTES
---
# T4 Docker and PostgreSQL Setup

## Metadata
- Owner: unassigned
- Created: 2026-11-21
- Updated: 2026-11-21

## Why Needed
The application has a runnable FastAPI foundation, but it lacks container packaging and a PostgreSQL service for Docker-based development.

## Objective
Add a Docker image definition and Docker Compose stack that runs the FastAPI application alongside PostgreSQL.

## Scope
- Add a Python application Dockerfile.
- Add a Docker Compose configuration with an application service and PostgreSQL service.
- Document Docker Compose startup and database defaults.
- Add Docker build-context exclusions.

## Non-Goals
- Run containers or database migrations.
- Add application database models or database-driver integration.
- Add production secrets, TLS, or deployment infrastructure.

## Target Files
- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`
- `README.md`
- `docs/workflow/changelog/2026-11`
- `docs/workflow/done/T4_docker_postgresql.md`

## Verification
- `.\\venv\\Scripts\\python.exe -m unittest discover .\\tests\\`
- Docker Compose configuration syntax check via `docker compose -f .\docker-compose.yml config --quiet`
- `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"`
- `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_done_task_evaluation_boundaries.py"`

## Rollback
Remove the Dockerfile, Compose file, Docker ignore file, README Docker section, and task/changelog files.

## Completion Artifact
Container configuration that packages the FastAPI app and declares a PostgreSQL service, plus documented local Compose usage and validation evidence.

Validation completed: the Docker Compose configuration syntax check exited successfully, all 7 repository unittest tests passed, and both markdown and done-task evaluation boundary tests passed.

PostgreSQL image correction: upgraded to the official
`postgres:18.7-alpine3.24` image and mounted the named volume at
`/var/lib/postgresql`, matching PostgreSQL 18's version-specific data layout.
