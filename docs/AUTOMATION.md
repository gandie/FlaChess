# Tournament Pairing Automation

## Purpose

This document prepares the first pairing-automation implementation for the
implemented `knockout`, `round_robin`, and `swiss` phase formats. It defines
the mechanics that can be derived from existing data, the shared generation
workflow, the validation boundaries, and the implementation slices.

This is a planning contract, not an authorization to invent tournament policy.
Manual round and pairing creation remains supported. No automatic pairing
behavior should be enabled until the decision gates at the end of this
document are resolved.

## Existing Foundation

Pairing automation can build on the current hierarchy:

```text
tournament
  -> phase (format)
    -> section (planned_round_count, lifecycle, participants)
      -> round (number)
        -> game (white participant, black participant, scores)
        -> round participant (paired, bye, unplayed, absent, awarded score)
```

The section's phase format selects the pairing algorithm. Section participants
are the pairing population. Games and round-participant records are the
persisted output; a separate pairing-plan entity is not needed for the first
implementation.

Current standings already provide points, rank, and configured tie-break
values. Generated rounds must therefore use the same database transaction and
domain services as manual operation so standings and future pairings observe
one coherent state.

## Terminology and Inputs

- **Seed order** is the stable participant ordering supplied before round one.
- **Round count** is the number of rounds planned for the section.
- **Pairing plan** is an in-memory, side-effect-free preview for one round.
- **Eligible participant** is a section member who participates in the target
  round under the section's selected absence/withdrawal policy.
- **Bye** is a round-participant record without a game and with an explicitly
  awarded score.
- **Pairing history** contains all earlier games between section participants.
- **Color history** contains earlier white/black assignments per participant.

The current model has ratings and `source_rank`, but no explicit initial
`seed_position`. Rating order can be a seed convention only if approved. An
arbitrary operator-defined seed order requires a persisted field or an
equivalent explicit seed list before the pairing engine is added.

## Round-Count Rules

For a section with `n >= 2` eligible initial participants:

| Format | Round-count rule | Operator input |
| --- | --- | --- |
| Swiss | `planned_round_count = r`, where `r` is chosen by the operator | Required; do not derive from `n` |
| Round-robin | `n - 1` for even `n`; `n` for odd `n` | Display as calculated; reject a different value |
| Knockout | `ceil(log2(n))` with a bracket padded to the next power of two | Display as calculated; reject a different value |

All completed sections must have a positive planned round count. If round-robin
or knockout automation is enabled for a section, its calculated count should be
stored or validated before the section becomes active. Swiss pairing must stop
before the configured round limit. A zero- or one-player field is not pairable.

Round rows remain created on demand. This avoids populating future Swiss
pairings before earlier results exist and keeps knockout entry dependent on
completed prior-round winners.

## Shared Generation Workflow

1. Load the active section, its phase format, participants, rounds, games,
   round-participant records, and latest standings.
2. Validate section lifecycle, target round number, planned round count,
   participant count, prior-round completeness, and uninterrupted numbering.
3. Resolve the approved seed order and determine the eligible participants for
   the target round.
4. Dispatch to one pure format-specific pairing function using domain values,
   not ORM mutation or JavaScript logic.
5. Validate the complete plan: no self-pair, no duplicate participant, no
   repeat violation, one color assignment per game, and one valid record per
   participant.
6. In one transaction, create the round, paired games, paired round-participant
   rows, and any explicit bye/absence records.
7. Commit once. On validation, conflict, or persistence failure, retain no
   partial round.
8. Return a named read model for the generated round, then refresh the existing
   operation and spectator views.

An engine must never overwrite an existing or partially manual round. The next
round number is `max(existing) + 1`; duplicate, skipped, or out-of-order
requests fail explicitly.

## Swiss Mechanics

Swiss round one pairs from the approved seed order. Later rounds pair
participants from the standings after the immediately preceding round.

The algorithm must perform score-group pairing, not only adjacent greedy
pairing. It should:

- rank eligible participants by current points, then the configured Swiss
  ordering keys;
- pair within the highest available score group before moving down;
- use bounded backtracking to avoid avoidable repeat pairings, invalid colors,
  or an impossible lower group;
- permit controlled score-group floaters only under the selected pairing
  profile;
- allocate one bye for an odd field under the selected bye policy;
- stop without writes when no legal complete matching exists.

The first implementation should expose a deterministic pairing profile rather
than a collection of ad-hoc booleans. Candidate profiles must define score
groups, float behavior, repeat tolerance, color rules, and tie ordering.
FIDE/Dutch-style rules require explicit selection and a conformance test set
before that profile can be claimed.

Standings snapshots are inputs. A Swiss section with a missing planned round
count cannot generate a round. A pairing request beyond that count is a
conflict.

## Round-Robin Mechanics

A single round-robin pairs every unordered participant pair exactly once.
For odd `n`, add one synthetic bye slot and use the circle method. For each
round, pair positions opposite one another, then rotate all but one fixed
position. The synthetic opponent identifies the real participant receiving a
bye.

The pure schedule can be precomputed from seed order:

- even field: `n - 1` rounds with `n / 2` games per round;
- odd field: `n` rounds with `(n - 1) / 2` games and one bye per round.

Color assignment is applied after the opponent schedule is produced. It must
be deterministic and balanced by the selected policy. A repeat is a
programming error for single round-robin and generation fails if the schedule
cannot cover every pair exactly once.

Double round-robin is not implied by the current `round_robin` enum. Supporting
it requires a separate approved representation because `planned_round_count`
alone cannot distinguish user error from intended double-round play.

## Knockout Mechanics

Choose a bracket size `b` as the smallest power of two greater than or equal to
`n`. The number of knockout rounds is `log2(b)`. The initial bracket maps the
approved seed order to bracket positions, including `b - n` byes.

For each later round:

- read only winners from the preceding completed round;
- pair winners in bracket order;
- preserve seed/bracket identity while advancing;
- create no next-round game until all predecessor matches have one winner;
- reject a completed draw unless an approved tie-resolution mechanism produces
  a winner.

The current game score model represents a single game outcome and has no
independent winner, leg, or match-series entity. A first knockout slice should
therefore support only a tournament policy that yields one decisive winner per
bracket game, or add an explicitly designed match/tie-break model first.
Third-place matches are outside the base bracket until approved.

## Color Allocation

Color allocation must be isolated behind one deterministic service shared by
all formats. Inputs are the pair, prior color history, initial seed/rank, and
format-specific policy. Outputs are only white and black participant IDs.

The allocator should prefer, in policy order:

1. no participant's repeat-color limit is exceeded;
2. color balance is improved;
3. no opponent-pairing constraint is lost merely to satisfy an inessential
   color preference;
4. unresolved ties use stable seed/ID order.

These are requirements for the service boundary, not final chess pairing
rules. The exact priorities, maximum consecutive colors, and first-round
allocation remain decision gates.

## Persistence and Integrity

Every generated real pairing creates one `Game` and two `RoundParticipant` rows
with `participation_type=paired`. Every automated bye creates one
`RoundParticipant` row with `participation_type=bye` and an approved awarded
score. Unplayed or absent outcomes remain explicit and are not silently
interpreted as byes.

Generation commands must validate:

- both game participants belong to the round's section;
- a participant appears at most once in a generated round;
- every eligible participant has one game or explicit non-paired outcome;
- pair and round uniqueness within the format's rules;
- paired participants do not also receive awarded round scores;
- no round is generated after the section is finished;
- no future round is generated while the prior round is incomplete.

The database's existing constraints remain the last line of defense. The
application layer must still provide specific domain conflicts rather than
relying on a generic integrity error.

## API and Operator Flow

Add one section-oriented command after the pure services and tests exist.
The command should generate the next round; clients should not submit arbitrary
white/black assignments to the automation endpoint.

Recommended response shape:

- section and round identity;
- format and target round number;
- calculated and planned round counts;
- generated games and non-paired outcomes;
- warnings or policy labels used by the selected profile.

The operator UI should add preview and confirm actions to the existing section
workspace. Preview runs the same pure engine without writes. Confirm reruns the
validation and writes transactionally, so preview is useful but never trusted
as stale authority. Manual creation remains a separate explicit path.

## Actionable Implementation Steps

1. Resolve the decision gates below and record the selected policy in this
   document.
2. Add pure pairing-domain types and round-count functions with exhaustive
   unit tests. Keep SQLAlchemy and FastAPI out of these tests.
3. Implement and independently verify round-robin circle scheduling,
   including odd-field byes and complete pair coverage.
4. Implement Swiss legal-matching with deterministic ordering, bounded
   backtracking, and no-database persistence.
5. Implement knockout bracket mapping and winner-only advancement, gated on a
   decisive-result policy.
6. Implement one color-allocation policy shared by the format engines.
7. Add a transactional `generate_next_round` domain command with lifecycle,
   numbering, completeness, and existing-round conflicts.
8. Add section API preview/confirm routes and explicit Pydantic read/command
   contracts; reuse operation read models where possible.
9. Add operator preview, confirmation, and result display without replacing
   manual pairing controls.
10. Update `docs/DATA.md`, `docs/DESIGN.md`, and user-facing examples with only
    the policies actually shipped.

## Required Tests

Pure-engine tests should cover:

- Swiss first round, score groups, pair-repeat avoidance, color history,
  float/backtracking, odd-field bye, and impossible-plan failure;
- round-robin even and odd fields, round-count calculation, exact pair
  coverage, no duplicates, and balanced schedule shape;
- knockout non-power-of-two fields, seed placement, byes, round progression,
  draw blocking, and bracket completion;
- deterministic output for identical inputs and different valid color/pair
  tie-break orders.

Route/transaction tests should cover active-section requirements, draft and
finished rejection, missing plan rejection, skipped/existing round conflicts,
incomplete prior-round rejection, atomic rollback, same-section enforcement,
and generated round visibility in operation/standings responses.

## Operator Decisions Required

1. **Seed persistence:** Should initial seed be rating-descending with a stable
   ID tie-break, or must operators assign arbitrary seed positions?
2. **Swiss profile:** Which pairing profile is authoritative (for example,
   FIDE Dutch-style), and which float/repeat preferences and tie ordering apply?
3. **Byes:** Who receives a bye, can a participant receive more than one, and
   is the awarded score always `1`, `0.5`, or format-dependent?
4. **Color policy:** What maximum consecutive-color imbalance is allowed, and
   what initial-round color rule and fallback order should be used?
5. **Knockout resolution:** Is a draw followed by another game, decided by a
   configured tie-break, or forbidden? Must tied-score results be represented
   as a multi-game match rather than one `Game` row?
6. **Round-robin scope:** Is the first slice single round-robin only, or is a
   double-round option required now?
7. **Absence and withdrawal:** Which existing `absent`/`unplayed` states affect
   eligibility in later rounds, and can a participant re-enter?

These choices affect public behavior and stored data. Implementation should not
silently select answers to them.

## Completion Criteria for the Implementation Slice

The automation implementation is complete only when a section with an explicit
approved policy can preview and transactionally generate the next legal round,
manual operation still works, round counts match the format, no partial data is
committed, and focused pure-engine plus route tests prove every format's
invariants.
