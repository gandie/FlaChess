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
# T33 Resolve Pairing Automation Policy

## Metadata
- Owner: unassigned
- Created: 2026-11-24
- Updated: 2026-11-24

## Why Needed
Pairing automation cannot be implemented safely while seed persistence, Swiss
pairing, byes, colors, knockout draws, round-robin scope, and withdrawal
semantics remain open. Each choice affects public behavior or stored data.

## Objective
Resolve and document every operator decision required for the first pairing
automation implementation slice.

## Scope
- Guide the operator through each decision with concrete examples.
- Record each accepted policy immediately in `docs/AUTOMATION.md`.
- Complete the decision phase when all seven policy gates are resolved.

## Non-Goals
- Implementing pairing engines or routes.
- Selecting policy defaults without explicit operator approval.

## Target Files
- `docs/AUTOMATION.md`
- `docs/workflow/tasks/T33_resolve_pairing_automation_policy.md`
- `docs/workflow/changelog/`

## Verification
- `.\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_markdown_boundaries.py"` passed (1 test).
- `.\\venv\\Scripts\\python.exe -m unittest discover .\\tests\\` passed (92
  tests).

## Rollback
Remove the policy decisions and restore the unresolved decision list in
`docs/AUTOMATION.md`; remove this task artifact if no decisions are retained.

## Completion Artifact
`docs/AUTOMATION.md` contains approved, unambiguous policies for all seven
operator decision gates, with the decisions reflected in this task record.
Markdown boundary validation and the full unittest suite passed.

## Decision Record
- Seed persistence: operator-assigned seed positions are authoritative.
  Pairing engines must not derive initial seeds from ratings because many
  players have no rating.
- Swiss profile: use FIDE Dutch-style pairing, with equal-score grouping,
  repeat avoidance, and bounded backtracking. For required downward floats,
  prefer the eligible player with the highest seed number; resolve ties by seed
  ascending and then stable player ID.
- Byes: in Swiss pairing, select the lowest-ranked participant without a
  previous bye, award 1 point, and enforce at most one bye. Fail explicitly if
  no eligible recipient remains. Round-robin and knockout structural byes do
  not use this score-awarding rule.
- Color policy: avoid a third consecutive same color when possible. Alternate
  the higher seed's initial color across pairings. Prioritize legal score-group
  pairing, repeat avoidance, streak avoidance, total color imbalance, and then
  deterministic seed/ID order.
- Knockout draws: a draw cannot advance a participant. Each generated pairing
  starts as one game; an unresolved draw blocks later generation until the
  operator manually records a decisive playoff game.
- Round-robin scope: first-slice automation supports exactly one cycle, so
  every eligible participant meets every other eligible participant once.
- Absence and withdrawal: absent or unplayed affects only that round. Explicit
  withdrawal removes later-round eligibility; explicit operator action is
  required for re-entry, without changing historical results.
