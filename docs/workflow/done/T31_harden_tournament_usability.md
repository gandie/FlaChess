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
# T31 Harden Tournament Usability

## Metadata
- Owner: unassigned
- Created: 2026-11-24
- Updated: 2026-11-24

## Why Needed
First tournament tests showed that operators must scroll extensively to reach
the game whose result they need to enter. Players also need a read-only
tournament display for following the current phase, round results, upcoming
games, and standings without using operator controls.

## Objective
Reduce the navigation and scrolling cost of dense tournament operation and add
a focused spectator tournament view built from existing API contracts.

## Scope
- Add a read-only tournament display for current phase, completed results,
  upcoming games, and standings.
- Add direct links and compact controls for faster round and result-entry
  navigation.
- Improve keyboard, focus, sticky-navigation, responsive, and accidental-action
  ergonomics in the affected views.
- Add focused static frontend coverage and update usage documentation.

## Non-Goals
- New pairing automation or tournament policy.
- Authentication or a separate permission model.
- Live push updates or unrelated backend workflow changes.

## Target Files
- `app/static/app.js`
- `app/static/display.js`
- `app/static/operations.js`
- `app/static/standings.js`
- `app/static/styles.css`
- `app/static/tournaments.js`
- `tests/test_tournament_usability.py`
- `tests/test_app.py`
- `docs/DESIGN.md`
- `README.md`
- `docs/workflow/changelog/2026-11`

## Verification
- `node --check` passed for `app\static\display.js`, `app\static\app.js`,
  `app\static\operations.js`, `app\static\standings.js`, and
  `app\static\tournaments.js`.
- Focused usability, section-operation, workspace, and app frontend suites
  passed (21 tests total).
- Markdown and refactor boundary validation passed.
- `.\\venv\\Scripts\\python.exe -m unittest discover .\\tests\\` passed
  (92 tests).

## Rollback
Remove the spectator route and compact-operation enhancements, restore the
previous frontend navigation and layout, and revert the task documentation.

## Completion Artifact
An operator can jump directly to a round and result editor with substantially
less page navigation, while a player can open a read-only tournament display
showing the active phase, game state, and latest available standings.
Result shortcuts prioritize incomplete games, saving a result moves focus to
the next incomplete editor, round controls stay available while scrolling,
and route changes restore focus to the page heading.
