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
# T41 Add Pairing Preview and Confirm API

## Metadata
- Owner: unassigned
- Created: 2026-11-24
- Updated: 2026-11-24

## Why Needed
The pure pairing planners and transactional generation command exist, but the
application has no explicit API boundary for operators to inspect a legal next
round before committing it. The operator flow needs a read-only preview and a
separate confirmation command that independently revalidates authoritative
state, rejects stale target rounds, and returns actionable domain failures.

## Objective
Add section-oriented pairing preview and confirmation routes with explicit
Pydantic contracts that reuse the existing planning and generation paths.

## Scope
- Add read-only preview and transactional confirmation section routes.
- Expose round identity, format, round counts, games, outcomes, seed order,
  policy labels, and warnings.
- Require the previewed target round during confirmation and revalidate state
  before invoking generation.
- Map missing sections, stale previews, invalid state, and persistence
  conflicts to actionable HTTP responses.
- Add focused route contract, stale-preview, no-write, and error tests.

## Non-Goals
- Section operation frontend controls or post-confirm navigation.
- Changes to pairing policy or pure format algorithms.
- Database schema changes or a replacement manual pairing path.

## Target Files
- `app/pairing/`
- `app/routes/`
- `app/*schemas.py`
- `tests/`
- `docs/AUTOMATION.md`
- `docs/workflow/changelog/`

## Verification
- `.\venv\Scripts\python.exe -m unittest tests.test_pairing_generation
  tests.test_pairing_generation_routes` passed (18 tests).
- `.\venv\Scripts\python.exe -m unittest discover -s tests -p
  "test_refactor_boundaries.py"` passed (1 test).
- `.\venv\Scripts\python.exe -m unittest discover -s tests -p
  "test_markdown_boundaries.py"` passed (1 test).
- `.\venv\Scripts\python.exe -m unittest discover .\tests\` passed (168 tests).

## Rollback
Remove the preview/confirm routes, contracts, focused tests, exports, and
workflow records; the existing transactional generation command remains.

## Completion Artifact
API tests prove preview performs no writes, confirmation independently
revalidates and commits through the transactional command, stale targets return a
conflict, and both routes expose the complete pairing read contract. The
section preview endpoint returns games, explicit outcomes, seed order, policy
labels, warnings, and round counts; confirmation requires an expected target
round and returns the persisted round identity.
