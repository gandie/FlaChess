# Tournament Pairing Automation

## Purpose

This document prepares the first pairing-automation implementation for the
implemented `knockout`, `round_robin`, and `swiss` phase formats. It defines
the mechanics that can be derived from existing data, the shared generation
workflow, the validation boundaries, and the implementation slices.

This is a planning contract, not an authorization to invent tournament policy.
Manual round and pairing creation remains supported. The decision gates were
resolved and recorded in
[T33](workflow/done/T33_resolve_pairing_automation_policy.md); implementation
must conform to those approved policies rather than introduce alternate
defaults.

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
`seed_position` or section-level withdrawal state. Because the approved policy
uses arbitrary operator-assigned seeds and explicit withdrawal/re-entry, those
states must be persisted and exposed before pairing automation is added.

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

This chain is dependency-ordered. Each step is complete only with its stated
validation, and the final steps must expose the generated behavior in the
existing operator workspace.

1. **Done — Resolve policy:** [T33](workflow/done/T33_resolve_pairing_automation_policy.md)
    recorded all seven approved decisions in this document. Do not reintroduce
    them as runtime defaults or silently alter them during implementation.
2. **Done — Persist and edit pairing prerequisites:**
    [T35](workflow/done/T35_persist_pairing_prerequisites.md) added
    operator-assigned, section-unique seed positions, explicit section-membership
    withdrawal state, migration and service validation, and section
    structure/operator controls. Draft activation rejects missing, duplicate, or
    invalid seeds for pairable fields. Withdrawal and re-entry are dedicated
    actions and leave historical games and scores unchanged.
3. **Done — Add the pure common pairing layer:**
    [T36](workflow/done/T36_add_common_pairing_layer.md) added side-effect-free
    input/output types, format-specific round-count functions, complete-plan
    validators, deterministic tie ordering, and the shared color allocator.
    SQLAlchemy and FastAPI remain outside this layer, and focused tests cover
    the approved first-round, streak, balance, and fallback rules.
4. **Done — Implement single round-robin:**
    [T37](workflow/done/T37_implement_single_round_robin.md) added a pure
    seed-ordered circle scheduler with independent schedule-shape and exact
    unordered-pair verification, scoreless structural byes, calculated round
    limits, and the shared color allocator. It returns an in-memory plan and
    performs no database access.
5. **Done — Implement Swiss:**
    [T38](workflow/done/T38_implement_swiss_pairing.md) adds FIDE/Dutch-style
    score-group matching from seeds or latest standings, minimum-repeat bounded
    backtracking with controlled down-floats, one-bye selection, explicit
    impossible-plan failure, and the shared color allocator. It returns an
    in-memory plan only.
6. **Implement knockout:** Map operator seeds into the padded bracket, create
    structural first-round byes, advance only completed decisive winners in
    bracket order, and reject drawn or unresolved predecessor matches. Return an
    in-memory plan only.
7. **Add transactional generation:** Implement a domain command that reloads
    authoritative section state, checks active lifecycle, planned/calculated
    round count, seed completeness, eligibility, uninterrupted numbering,
    previous-round completeness, and existing-round conflicts, then creates the
    complete round, games, and round-participant records in one commit.
    Any domain or persistence failure must roll back everything.
8. **Add preview and confirm API contracts:** Add section-oriented preview and
    confirm routes with explicit Pydantic read/command models. Preview calls the
    same pure planning path without writes. Confirm independently reloads and
    validates state before calling the transactional command; a stale preview is
    never an authorization token. Responses must expose target round, format,
    games, byes/non-paired outcomes, seed order, policy labels, warnings, and
    actionable domain errors.
9. **Integrate the section operation UI:** In
    `app/static/operations.js`, add a visible **Preview next round** action for
    eligible active sections. Render the returned pairing table, colors, byes,
    warnings, and next round number; provide a separate **Confirm generation**
    action; and display backend conflicts without discarding the operator's
    context. Preserve the existing manual round/pairing path.
10. **Complete the post-confirm workflow:** After confirmation, navigate to or
     refresh the generated round, refresh operation/standings data, focus its
     result-entry controls, and let the operator record results with the
     existing game editor. Once that round is complete, recompute standings
     and make the next preview available. Ensure spectator/display responses see
     the committed generated round through the existing operation contract.
11. **Prove the operator journey and document it:** Add end-to-end route/UI
     coverage for every format from preview through confirmation, result entry,
     standings visibility, and next-round availability, including stale preview,
     conflict, rollback, and manual fallback paths. Update `docs/DATA.md`,
     `docs/DESIGN.md`, README usage, and any operator examples only after the
     tested behavior ships.

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
generated round visibility in operation/standings/display responses, stale
preview rejection, and error responses usable by the frontend.

Frontend tests should cover visibility of preview/confirm controls only in
eligible active sections, preview tables and warnings, confirm behavior,
non-destructive conflict display, manual pairing coexistence, post-confirm
navigation/refresh, result-entry focus, and next-round availability.

## Approved Operator Decisions

1. **Seed persistence — decided:** Operators assign arbitrary seed positions.
   Stored seed positions are authoritative; pairing engines do not derive
   initial seeds from ratings. This is required for players without ratings.
2. **Swiss profile — decided:** Use a FIDE Dutch-style profile. Pair within
   score groups where possible, avoid repeat opponents where possible, and use
   bounded backtracking for a legal plan. When a downward float is required,
   select the eligible player with the highest seed number first. Resolve ties
   deterministically by seed ascending, then stable player ID.
3. **Byes — decided:** In Swiss pairing, select the lowest-ranked eligible
   player who has not previously received a bye. A bye awards `1` point and a
   participant may receive at most one. If every active participant has already
   received a bye, generation fails explicitly rather than granting a second
   one. Round-robin schedule placeholders and knockout bracket advancements are
   structural byes, not score-awarding Swiss byes.
4. **Color policy — decided:** Avoid giving a participant the same color three
   times consecutively whenever the current pairing plan permits. In the first
   Swiss round, alternate the higher-seeded participant's color across
   top-versus-bottom pairings: White for pair 1, Black for pair 2, White for
   pair 3, and so on. Color fallback priority is: legal score-group pairing,
   repeat-opponent avoidance, avoid a third consecutive color, minimize
   total White-minus-Black imbalance, then deterministic seed/ID order.
5. **Knockout resolution — decided:** A draw is forbidden from advancing a
   participant. One generated knockout pairing initially creates one `Game`;
   a drawn or tied result leaves the match unresolved and blocks later-round
   generation. The operator must record a separate decisive playoff game
   manually; automatic rematches, tie-break winners, and multi-game match
   aggregation are outside the first slice.
6. **Round-robin scope — decided:** The first slice supports single
   round-robin only. Every participant is scheduled against every other
   participant once; a double-round option remains future work.
7. **Absence and withdrawal — decided:** An `absent` or `unplayed` result
   affects only its own round and does not automatically remove the participant
   from later-round eligibility. Only an explicit withdrawal makes the
   participant ineligible. Re-entry is allowed only through an explicit
   operator action, and historical results remain unchanged.

These choices affect public behavior and stored data. Implementation should not
silently select answers to them.

## Completion Criteria for the Implementation Slice

The automation implementation is complete only when an operator can open an
active section, preview the next legal round, understand its pairings/colors/
byes and warnings, confirm generation, see the persisted round in the existing
workspace, record its results, recompute standings, and preview the following
round without using an API client or database tool. Manual operation must still
work, round counts must match the format, no partial data may be committed, and
pure-engine, route, transaction, frontend, and end-to-end tests must prove every
format's invariants and the failure paths.
