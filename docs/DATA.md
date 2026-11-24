# Data Model

DATA.md is the main data structure design document for Fla Chess. The tables
below are implemented with SQLAlchemy models and Alembic migrations.

## Implementation Status: Complete

All 12 entities documented here have an SQLAlchemy model, an Alembic-created
SQL table, and a registered SQLAdmin view. Pairing preview and confirmation are
implemented application behavior over this model; tournament advancement and
additional tie-break formulas remain application work rather than missing data
entities.

## Implemented Tables

### `player`

Stores player names.

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | `BIGINT` | Generated primary key |
| `name` | `VARCHAR(255)` | Not null |

Player names are not constrained to be unique.

### `tournament`

Stores tournament metadata and lifecycle state.

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | `BIGINT` | Generated primary key |
| `name` | `VARCHAR(255)` | Required; 1–255 characters |
| `description` | `TEXT` | Optional free text |
| `lifecycle` | `VARCHAR(20)` | `draft`, `active`, or `finished` |
| `time_control` | `VARCHAR(255)` | Optional |
| `starts_at` | `TIMESTAMPTZ` | Optional planned start |
| `ends_at` | `TIMESTAMPTZ` | Optional; after `starts_at` when both exist |

New tournaments default to `draft`. Lifecycle updates are route-controlled:
activation requires at least two registered players, then the only allowed path
is `draft → active → finished`.

### `tournament_participant`

Represents a player's explicit tournament registration.

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | `BIGINT` | Generated primary key |
| `tournament_id` | `BIGINT` | Foreign key to `tournament.id`; not null |
| `player_id` | `BIGINT` | Foreign key to `player.id`; not null |

The unique `(tournament_id, player_id)` pair prevents duplicate registration.
Deleting a row unregisters the player. Registrations have no lifecycle state.

## Shared Modeling Conventions

The following conventions apply to existing and future SQLAlchemy entities:

- Every database entity uses a generated `BIGINT` primary key named `id`.
- Foreign-key columns use `BIGINT` so key types remain consistent.
- Fixed application enums use `VARCHAR` columns with database check constraints
  and typed Python enums. PostgreSQL-native enum types are not used, keeping
  schemas easier to migrate to SQLite or other relational databases.
- Required string fields use `VARCHAR` with an explicit maximum length.
- Optional names and comments use nullable columns unless a later requirement
  makes them mandatory.
- Use SQLAlchemy 2 mapped classes and Alembic migrations for schema changes.
- Database constraints should enforce invariants that can be represented in SQL;
  business rules that require tournament context remain in application logic.
- Unique constraints are only added after the exact domain identity is defined.
- Planned relationships use SQLAlchemy mapped relationships only after the
  migration schema has been designed.

## Implemented Tournament Tables

### `section_participant`

Represents one tournament participant's membership in a phase section.

| Column | Type | Constraints / Notes |
| --- | --- | --- |
| `id` | `BIGINT` | Generated primary key |
| `participant_id` | `BIGINT` | Foreign key to `tournament_participant.id`; not null |
| `section_id` | `BIGINT` | Foreign key to `tournament_section.id`; not null |
| `rating` | `INTEGER` | Optional rating snapshot used by tie-break calculations |
| `rating_source` | `VARCHAR(64)` | Optional source identifier for the rating snapshot |
| `source_section_id` | `BIGINT` | Optional section from which this membership advanced |
| `source_rank` | `INTEGER` | Optional rank in the source section used for assignment |

A unique constraint on `(participant_id, section_id)` prevents duplicate
membership of one tournament participant in the same section.

Membership in later sections preserves advancement history instead of replacing
the participant's earlier membership. Section reassignment is implemented by
adding/removing membership rows.
When a participant advances from one section to another, `source_section_id`
and `source_rank` preserve the assignment basis. An initial participant has
nullable source fields.

Section participation may retain optional fine-grained tie-break inputs. The
initial design names `rating`; other inputs may be added later if an explicit
tie-break formula requires them.

### `tournament_phase`

Represents a stage within a tournament.

A phase allows tournaments to combine formats. For example, players may advance
from a group qualification phase into a knockout phase. A phase may contain
multiple rounds or tables, depending on the selected format.

Fields:

| Column | Type | Constraints / Notes |
| --- | --- | --- |
| `id` | `BIGINT` | Generated primary key |
| `tournament_id` | `BIGINT` | Foreign key to `tournament.id`; not null |
| `sequence` | `INTEGER` | Ordered position inside the tournament |
| `format` | `VARCHAR` | Fixed enum: `knockout`, `round_robin`, `swiss` |

A unique constraint on `(tournament_id, sequence)` should prevent duplicate
phase ordering.

### `tournament_section`

Represents a table or section within a tournament phase. A section may contain
a subset of participants and its own rounds.

Fields:

| Column | Type | Constraints / Notes |
| --- | --- | --- |
| `id` | `BIGINT` | Generated primary key |
| `phase_id` | `BIGINT` | Foreign key to `tournament_phase.id`; not null |
| `name` | `VARCHAR(255)` | Required section name |
| `sequence` | `INTEGER` | Ordered position inside the phase |
| `lifecycle` | `VARCHAR(20)` | `draft`, `active`, or `finished` |
| `tie_break_locked_at` | `TIMESTAMPTZ` | Optional freeze time for configured tie-break rules |
| `planned_round_count` | `INTEGER` | Optional planned number of rounds in this section |
A unique constraint on `(phase_id, sequence)` prevents duplicate section
ordering. `planned_round_count` can be checked when a section is completed.
Transitions are explicit and strict: `draft → active → finished`. Activation
locks tie-break configuration in `tie_break_locked_at`; no round starts a
section automatically.

Phase formats are fixed application enums for now. PostgreSQL lookup-table
entities may replace or supplement these values later if a format needs
additional configuration or rules data.

### `tournament_round`

Represents one numbered round in a tournament phase.

Fields:

| Column | Type | Constraints / Notes |
| --- | --- | --- |
| `id` | `BIGINT` | Generated primary key |
| `section_id` | `BIGINT` | Foreign key to `tournament_section.id`; not null |
| `number` | `INTEGER` | Positive round number |

A unique constraint on `(section_id, number)` should prevent duplicate rounds
within a section.

### `game`

Represents a match within a tournament round.

Fields:

| Column | Type | Constraints / Notes |
| --- | --- | --- |
| `id` | `BIGINT` | Generated primary key |
| `round_id` | `BIGINT` | Foreign key to `tournament_round.id`; not null |
| `white_participant_id` | `BIGINT` | Foreign key to `section_participant.id`; not null |
| `black_participant_id` | `BIGINT` | Foreign key to `section_participant.id`; not null |
| `white_score` | `NUMERIC(2,1)` | Nullable; score is `0`, `0.5`, or `1` |
| `black_score` | `NUMERIC(2,1)` | Nullable; score is `0`, `0.5`, or `1` |
| `result_type` | `VARCHAR(32)` | `normal`, `white_forfeit`, `black_forfeit`, `double_forfeit`, or `adjusted` |
| `recorded_at` | `TIMESTAMPTZ` | Optional time the final result was recorded |
| `comment` | `TEXT` | Optional record of result changes, forfeit reasons, or related notes |

Both player scores in a game must sum to `1`. A draw is `0.5` plus `0.5`.
Both scores remain nullable until the result is recorded. Neither a second
game state field nor a game state machine is planned.

SQL constraints should ensure:

- both scores are present together or both are null;
- when present, each score is one of `0`, `0.5`, or `1`;
- when present, the two scores sum to `1`.
- white and black participants are different IDs.

The same-section condition cannot be guaranteed by a direct foreign-key
constraint alone because the round and both section memberships must be joined.
It should be enforced transactionally in pairing/application logic and may later
be reinforced with PostgreSQL triggers if that invariant becomes critical.

Forfeit and changed-result reasons belong in `comment`; a new result/status
enum is not added by default.

Game integrity constraints should ensure:

- a game has two different section participants;
- both participants belong to the round's section;
- a participant is not paired against themselves.

Duplicate-pair rules are format-dependent pairing concerns and are not enforced
at the base Game table level.

Both game participants must belong to the round's section. This is enforced by
their `section_participant.id` references; additional application validation
should reject pairs from different sections.

Pairings are represented by `game` rows. Each round may contain generated,
changed, or manually adjusted game rows. Pairing-plan entities are not planned
for the first implementation.

#### Pairing generation writes

Pairing preview is read-only. It loads the active section, authoritative seed
order, prior rounds, games, participation records, and tie-break rules, then
returns an in-memory Swiss, round-robin, or knockout plan without creating
rows. Confirmation independently reloads and validates the expected target
round; a stale preview is not accepted as authorization to write.

A successful confirmation creates the complete `tournament_round`, its
`game` rows, and the `round_participant` rows for paired players and any
non-paired outcomes in one transaction. Constraint or commit failures roll the
whole generation back and return a conflict. Once committed, the existing
round, operation, standings, and player-display contracts expose the generated
rows. Manual rounds, games, and participation records continue to use the same
tables and remain available as operator fallbacks.

### `round_participant`

Represents the participation outcome of one section participant in one round.
This entity covers paired, bye, forfeit, absent, and unplayed-round records that
cannot be derived safely from `game` alone.

| Column | Type | Constraints / Notes |
| --- | --- | --- |
| `id` | `BIGINT` | Generated primary key |
| `round_id` | `BIGINT` | Foreign key to `tournament_round.id`; not null |
| `participant_id` | `BIGINT` | Foreign key to `section_participant.id`; not null |
| `participation_type` | `VARCHAR` | `paired`, `bye`, `unplayed`, or `absent` |
| `score_awarded` | `NUMERIC(2,1)` | Nullable tournament point awarded outside a normal game |
| `comment` | `TEXT` | Optional reason or result note |

A unique constraint on `(round_id, participant_id)` prevents duplicate round
records. `score_awarded` is mutually exclusive with a normal paired `game`.

Examples:

- A paired round has a normal `game` and usually no `score_awarded`.
- A forfeit win may use normal `game` scores plus `game.result_type`.
- A bye may use a `round_participant` row with `participation_type=bye`.
- An unplayed round uses `participation_type=unplayed`; tie-break virtual-
  opponent handling reads this row.

### `section_tiebreak`

Stores the ordered tie-break list for a section. The operator configures it
while the section is `draft`; activation freezes the list before play.

| Column | Type | Constraints / Notes |
| --- | --- | --- |
| `id` | `BIGINT` | Generated primary key |
| `section_id` | `BIGINT` | Foreign key to `tournament_section.id`; not null |
| `code` | `VARCHAR(64)` | Portable tie-break identifier |
| `sequence` | `INTEGER` | Positive position in the ordered list |
| `parameter` | `VARCHAR(255)` | Optional JSON-free parameter string |
| `is_active` | `BOOLEAN` | Whether this rule is currently in the section list |

The database enforces unique `(section_id, sequence)` ordering and unique
`(section_id, code, parameter)` configuration, including repeated null
parameters. Parameters remain opaque strings until ranking implementation
requires structured values.

Known initial `code` values include:

- `direct_encounter`
- `number_of_wins`
- `progressive_score`
- `buchholz`
- `buchholz_cut_1`
- `buchholz_cut_2`
- `buchholz_median_1`
- `buchholz_median_2`
- `fore_buchholz`
- `sonneborn_berger`
- `sonneborn_berger_cut_1`
- `koya`
- `average_rating_of_opponents`
- `tournament_performance_rating`
- `perfect_tournament_performance`
- `rating`

The exact configuration can extend this list through a later lookup table or
Python enum. The data model does not require implementation of every code.

### `section_standing`

Stores a recomputable standings snapshot for a section. It may be created after
each round or only at tournament completion.

| Column | Type | Constraints / Notes |
| --- | --- | --- |
| `id` | `BIGINT` | Generated primary key |
| `section_id` | `BIGINT` | Foreign key to `tournament_section.id`; not null |
| `participant_id` | `BIGINT` | Foreign key to `section_participant.id`; not null |
| `through_round_id` | `BIGINT` | Optional foreign key to `tournament_round.id` |
| `rank` | `INTEGER` | Optional provisional or final rank |
| `points` | `NUMERIC(6,1)` | Primary match-point total |
| `wins` | `INTEGER` | Count of wins |
| `draws` | `INTEGER` | Count of draws |
| `losses` | `INTEGER` | Count of losses |
| `game_points` | `NUMERIC(6,1)` | Optional format-specific secondary total |
| `computed_at` | `TIMESTAMPTZ` | Required calculation timestamp |

A null `through_round_id` identifies the whole-section snapshot. The unique
snapshot key is `(section_id, participant_id, coalesce(through_round_id, 0))`.
Recomputation atomically replaces every standing and value for one key while
preserving other snapshots; equal ranking vectors share a competition rank.

### `section_standing_value`

Stores one normalized tie-break value for a section standing.

| Column | Type | Constraints / Notes |
| --- | --- | --- |
| `id` | `BIGINT` | Generated primary key |
| `standing_id` | `BIGINT` | Foreign key to `section_standing.id`; not null |
| `tiebreak_id` | `BIGINT` | Foreign key to `section_tiebreak.id`; not null |
| `sequence` | `INTEGER` | Copied rule position for stable historical output |
| `value` | `NUMERIC(12,4)` | Calculated tie-break value |

This normalized list preserves the exact configured order used for ranking.

The calculator uses completed game scores and non-paired awarded round scores.
It supports direct encounter, wins, progressive score, Buchholz Cut/Median
variants, and Sonneborn-Berger variants; unsupported codes fail explicitly.
## Example Tournament Consistency Check

The model supports the following concrete tournament:

| Structure | Stored representation |
| --- | --- |
| 16-player blitz 3+2 tournament | One `tournament`, `name`, `time_control="3+2"` |
| Qualification phase, 5 Swiss rounds | Phase 1 with `format=swiss`; one section with `planned_round_count=5` |
| Beginner and advanced groups | Two sections in Phase 2, both with `format=swiss` and `planned_round_count=7` |
| 8 initial players per final section | `section_participant` rows, 8 per section, with source section/rank fields |

For qualification, all 16 tournament participants receive
`section_participant` membership in one qualification section. After five rounds,
write eight membership rows for each second-phase section. These rows retain
`source_section_id` and `source_rank`.

The beginner/advanced split rule is application logic; DATA.md does not require
a hard-coded rule.

For each 7-round section, `tournament_round.number` is 1 through 7 and games
use section participants. Section standings retain rank and tie-break values.

## Lifecycle State Conventions

Tournament states are modeled as lifecycles. The initial states are:

- `draft`
- `active`
- `finished`

The initial Tournament transition graph is strict:

- `draft → active`
- `active → finished`

Other transitions are forbidden. Reopening a finished tournament or allowing
administrative edits after completion must be implemented later as explicit
transition additions with defined `on_leave` and `on_enter` consequences.

The `draft → active` transition is guarded by tournament context. The
Tournament's `draft` lifecycle `on_leave` hook must verify that at least two
players are registered. Additional activation checks should use the same hook
area later.

Lifecycle transition methods must receive the relevant Tournament context,
including access to its participant data. Business-rule failures raised by
lifecycle hooks are user-facing business errors and must be returned upward
through FastAPI rather than represented as internal system errors.

A lifecycle implementation must follow one standardized state-machine pattern.
Business logic triggered by transitions belongs in lifecycle hooks:

- `on_enter`
- `on_leave`

All lifecycle fields and implementations should use the same convention rather
than defining one-off callback names or transition behavior per entity.
Future lifecycle models should document their allowed transitions explicitly
before implementation.

The Tournament lifecycle follows this pattern.

## Completed Data-Structure Roadmap

The implemented hierarchy is:

`tournament → tournament_phase → tournament_section → section_participant`

The implementation slices for tournament records, structure and membership,
rounds and participation outcomes, tie-break configuration, and standings
snapshots are complete. The remaining roadmap concerns application behavior,
including pairing automation, advancement, and additional ranking rules.
