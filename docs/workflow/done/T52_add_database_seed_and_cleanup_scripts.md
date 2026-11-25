---
agent_evaluation:
  version: 1
  evaluator: human_operator
  evaluated_at: 2026-11-25
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

# T52 Add Database Seed and Cleanup Scripts

## Metadata
- Owner: unassigned
- Created: 2026-11-25
- Updated: 2026-11-25

## Why Needed
Developers need repeatable local tournament and player data for exercising the
application, plus a complete reset path that removes all tournament-owned data
and restores generated identifiers before the next test run.

## Objective
Add SQL tools beside the existing PowerShell PostgreSQL helper for populating
random-looking player and tournament names and fully truncating tournaments and
players.

## Scope
- Add a PostgreSQL seed script for player and draft tournament rows.
- Add a PostgreSQL cleanup script that truncates tournament and player roots
  with identity reset and dependent-row cleanup.
- Extend the existing PowerShell helper to execute SQL files.
- Document and test the database tool contracts.

## Non-Goals
- Seed tournament phases, sections, rounds, games, or standings.
- Change production database schema or application behavior.

## Target Files
- tools/psql.ps1
- tools/seed_database.sql
- tools/cleanup_database.sql
- tests/test_database_tools.py
- README.md

## Verification
- Focused database tool contracts passed: 3 tests.
- Full unittest discovery passed: 181 tests.
- Markdown boundary validation passed: 1 test.
- PowerShell parser validation passed for `tools/psql.ps1`.
- `git diff --check` passed.
- A live `SELECT 1` through the existing inline helper returned one row.

## Rollback
Remove the SQL scripts, revert the helper and README changes, and remove the
focused test and workflow records.

## Completion Artifact
The tools directory contains documented SQL seed and cleanup scripts, and the
existing PowerShell helper can execute either inline SQL or either SQL file
against the Compose PostgreSQL database. The seed inserts 24 randomized player
name combinations and three randomized draft tournament names; cleanup
truncates both root tables with cascading dependent-row deletion and identity
reset. Destructive seed and cleanup execution was intentionally not run against
the existing shared Compose dataset during validation.
