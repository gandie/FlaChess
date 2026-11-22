# Data Model

DATA.md is the main data structure design document for Fla Chess. It distinguishes
what is implemented today from entities that are planned. Planned entities are
design notes, not database or migration commitments.

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

## Planned Tables

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

Likely fields:

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

Likely fields:

| Column | Type | Constraints / Notes |
| --- | --- | --- |
| `id` | `BIGINT` | Generated primary key |
| `phase_id` | `BIGINT` | Foreign key to `tournament_phase.id`; not null |
| `name` | `VARCHAR(255)` | Required section name |
| `sequence` | `INTEGER` | Ordered position inside the phase |
| `tie_break_locked_at` | `TIMESTAMPTZ` | Optional freeze time for configured tie-break rules |
| `planned_round_count` | `INTEGER` | Optional planned number of rounds in this section |
A unique constraint on `(phase_id, sequence)` should prevent duplicate section
ordering. Separate section membership is handled by participant assignments.
`planned_round_count` may be compared with the count of `tournament_round`
records when a section is activated or completed.

Phase formats are fixed application enums for now. PostgreSQL lookup-table
entities may replace or supplement these values later if a format needs
additional configuration or rules data.

### `tournament_round`

Represents one numbered round in a tournament phase.

Likely fields:

| Column | Type | Constraints / Notes |
| --- | --- | --- |
| `id` | `BIGINT` | Generated primary key |
| `section_id` | `BIGINT` | Foreign key to `tournament_section.id`; not null |
| `number` | `INTEGER` | Positive round number |

A unique constraint on `(section_id, number)` should prevent duplicate rounds
within a section.

### `game`

Represents a match within a tournament round.

Likely fields:

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

Stores the ordered tie-break list for a section. The operator may configure it
before the first round and should be able to freeze it when the section starts.

| Column | Type | Constraints / Notes |
| --- | --- | --- |
| `id` | `BIGINT` | Generated primary key |
| `section_id` | `BIGINT` | Foreign key to `tournament_section.id`; not null |
| `code` | `VARCHAR(64)` | Portable tie-break identifier |
| `sequence` | `INTEGER` | Positive position in the ordered list |
| `parameter` | `VARCHAR(255)` | Optional JSON-free parameter string |
| `is_active` | `BOOLEAN` | Whether this rule is currently in the section list |

Unique constraints should cover `(section_id, sequence)` and
`(section_id, code, parameter)`. Parameters are intentionally opaque strings;
known numeric parameters may use an additional `parameter_value` decimal field
when ranking implementation is started.

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

A standing can be for the whole section by leaving `through_round_id` null.
The application must define the exact snapshot key and avoid duplicate
snapshots for the same section, participant, and completed round.

### `section_standing_value`

Stores one normalized tie-break value for a section standing.

| Column | Type | Constraints / Notes |
| --- | --- | --- |
| `id` | `BIGINT` | Generated primary key |
| `standing_id` | `BIGINT` | Foreign key to `section_standing.id`; not null |
| `tiebreak_id` | `BIGINT` | Foreign key to `section_tiebreak.id`; not null |
| `sequence` | `INTEGER` | Copied rule position for stable historical output |
| `value` | `NUMERIC(12,4)` | Calculated tie-break value |

This normalized value list avoids storing a JSON blob and preserves the exact
configured rule order used for ranking. Recomputing standings replaces or
supersedes their snapshot values.

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

## TODO

### Second implementation slice: structure and membership

- [x] Add the Tournament Phase model and Alembic migration.
- [x] Add the Tournament Section model and Alembic migration.
- [x] Add the Section Participant model and Alembic migration.
- [x] Add phase, section, and membership Pydantic schemas.
- [x] Add FastCRUD routes and SQLAdmin relationship selectors.
- [x] Enforce uniqueness, positive values, and the fixed phase-format enum.
- [x] Reject membership whose participant belongs to another tournament.
- [x] Add model, constraint, schema, and route tests.

This slice establishes the implemented hierarchy:

`tournament → tournament_phase → tournament_section → section_participant`

It enables formats, sections, assignments, ratings, advancement history,
planned rounds, and tie-break locking without pairing or ranking.

### Following implementation slices

#### Third slice: rounds, pairings, and participation outcomes

- [ ] Implement `tournament_round`.
- [ ] Implement `round_participant`.
- [ ] Implement `game`.
- [ ] Enforce score, participant, round-number, and participation constraints.
- [ ] Enforce that game participants belong to the round's section in
  application logic.

#### Fourth slice: tie-break configuration

- [ ] Implement `section_tiebreak`.
- [ ] Add ordered, unique configuration constraints and SQLAdmin controls.
- [ ] Add lifecycle behavior for freezing tie-break configuration when a
  section starts.

#### Fifth slice: standings snapshots

- [ ] Implement `section_standing` and `section_standing_value`.
- [ ] Define snapshot identity, recomputation, and ranking services.
- [ ] Add focused tie-break calculation tests.

- [x] Decide the minimum fields for the first `tournament` implementation.
- [x] Initial Tournament fields include name, description, lifecycle, time_control, starts_at, and ends_at.
- [x] Tournament dates are optional; ends_at must follow starts_at when both exist.
- [x] Tournament format belongs to phases; a Tournament may instead store free-text `description`.
- [x] Phase format uses fixed enums: `knockout`, `round_robin`, `swiss`.
- [x] Choose the initial Tournament lifecycle states: `draft`, `active`, `finished`.
- [x] Tournament lifecycle transitions are strict: `draft -> active -> finished`.
- [x] Draft activation requires at least two registered players in the draft lifecycle `on_leave` hook.
- [x] Tournament participation is a simple registered-row model; deleting its row unregisters the player.
- [x] Tournament activation requires at least two registered players.
- [x] Tournament participants have no registration lifecycle states.
- [x] Tournament participants are joined to sections through `section_participant`.
- [x] Phase/section membership and round ownership are structured as tournament -> phase -> section -> round -> game.
- [x] Game participants reference `section_participant.id`.
- [x] Pairings are stored as `game` rows inside a round; separate pairing-plan entities are not planned initially.
- [x] Unfinished games use nullable scores; forfeits and changed results use comment text.
- [x] Game integrity requires distinct participants who belong to the round's section.
- [x] Add SQL constraints for allowed game scores and distinct participant identity.
- [x] Tie-break requirements were researched; the complete raw and configuration entities are documented.
- [x] Tournament sections have planned round counts.
- [x] Later-section membership preserves source section and source rank.
- [x] The 16-player two-phase Swiss example has a documented representation.
- [ ] Implement `round_participant`, `section_tiebreak`, `section_standing`, and `section_standing_value` as later tournament entity tasks.
