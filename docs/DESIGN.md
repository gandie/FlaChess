# Project Design

## Purpose

Build a simple yet powerful system for organizing blitz chess tournaments with
eight or more players. The system will keep track of players, matches, score
tables, and related tournament information.

## Initial Technical Direction

- **Backend:** Python with FastAPI.
- **Frontend:** A simple static frontend, served by the FastAPI application.
- **Database:** PostgreSQL, connected to the FastAPI backend.
- **Local stack:** Docker Compose will run the application and database together.

## Initial Implementation Sequence

Establish and start the base infrastructure with Docker Compose early, before
implementing the API, frontend, or tournament behavior. This allows the
application and database stack to be brought up and checked independently of
those later features.

## Tournament Specification

- Support knockout, round-robin, and group/round/table formats using Swiss
  pairing rules.
- Tournament phases may be combined. A later phase may select participants from
  an earlier phase, such as players advancing from a group qualification round
  into a knockout stage.
- A blitz time control is tournament metadata only. It does not affect match
  scheduling or scoring mechanics.

## Match and Scoring Specification

- Store each player's match score in SQL. A score is `0`, `0.5`, or `1`.
- The two players' scores must total `1`. A draw is therefore represented as
  `0.5` for both players.
- Additional match information may be stored in a comment field, for example
  to record that a result was changed to a forfeit.
- Optional fine-grained rating fields may be retained for tie-break calculations.
  The initial implementation does not define a specific tie-break formula.

## Player and Tournament Data

- Players are initially managed by the single operator and identified by the
  name supplied during registration.
- The system supports multiple tournaments and retains tournament results in
  PostgreSQL.
- Player assignment to tournament phases and tables is handled by the operator
  or the applicable tournament format.

## Operation and Access

- The initial deployment assumes one operator using a physically protected system.
- Authentication and access control are not required for the initial system.
- The stack is intended to be manageable through Docker Compose, for example
  by using `docker compose up --build`.
- Deployment location and managed backup/recovery policies are intentionally
  unspecified. PostgreSQL's Docker volume is the local persistence boundary,
  and operators may back it up as appropriate.

## Frontend

The frontend is a single-page application for one tournament operator. It
must support the full workflow from creating a draft tournament through
registration, section operation, standings, and closeout. The browser is a
client of the existing FastAPI application, not a second source of tournament
rules or data integrity.

### Frontend Constraints

- Use semantic HTML, plain CSS, and browser-native JavaScript modules.
- Keep dependencies and third-party frameworks to the minimum required for the
  feature being delivered; the first implementation requires no frontend
  framework or build step.
- Serve the UI and its static assets from the FastAPI application.
- Use URL-backed screen state so refresh, back, and forward navigation do not
  lose the operator's current location.
- Keep the backend authoritative for lifecycle, relationship, score, and
  tie-break invariants. Client validation improves usability but does not
  replace server errors.
- Show loading, empty, validation, conflict, and unavailable-backend states
  explicitly. Destructive and lifecycle actions require clear confirmation.
- Use responsive, keyboard-accessible controls and avoid requiring mouse-only
  interactions during live tournament operation.
- Preserve the unauthenticated, single-operator assumption. Authentication,
  authorization, real-time synchronization, and multi-user conflict handling
  are not part of the first frontend implementation.

### Operator Screens

The initial SPA needs these connected views rather than a single undifferentiated
form:

1. **Tournament list**
   - Show draft, active, and finished tournaments with useful status and date
     information.
   - Create a tournament and open its workspace.
2. **Tournament overview**
   - Show and edit draft metadata while allowed.
   - Display readiness, lifecycle, registered-player count, phases, sections,
     and the available next action.
   - Activate or finish the tournament only through the existing transition
     actions.
3. **Player registration**
   - Maintain the reusable player registry.
   - Register and unregister tournament participants.
   - Assign registered participants to draft sections, including optional rating
     data.
4. **Structure and rules**
   - Create and order phases and sections.
   - Set planned round counts.
   - Configure the ordered tie-break list before section activation.
   - Make the tie-break lock caused by section activation visible.
5. **Section operation**
   - Activate a section, create rounds, and display round membership.
   - Create manual pairings and record or correct game results.
   - Record paired, bye, unplayed, and absent participation outcomes.
   - Recompute and display standings and tie-break values after results change.
6. **Closeout and history**
   - Finish a section, preserve its final standings, and show its planned-round
     status.
   - Display advancement membership and source section/rank for later phases
     when entered manually.
   - Finish the tournament and present an uncluttered read-only result view.

### SPA Foundation

Before feature screens, establish one small API client and a shared set of
interaction primitives:

- centralized `fetch` handling for JSON, network failures, `404`, validation
  errors, conflicts, and unexpected responses;
- a URL router and view lifecycle that prevents abandoned navigation from
  overwriting the current screen;
- reusable rendering and form behavior for fields, tables, status badges,
  confirmations, empty states, and pending actions;
- consistent mapping for IDs, ISO dates, `Decimal` values serialized as JSON,
  and enum values;
- explicit refresh after successful writes, rather than an independently
  maintained browser copy of backend state.

The frontend should be split into small static HTML, CSS, and JavaScript
modules when the first screen needs that separation. Files should not be split
only to satisfy an anticipated future framework structure.

### API Contract Strategy

The generic CRUD routes are the source for individual records, but they are not
automatically suitable as screen contracts. A screen should not have to
discover a tournament by issuing an unbounded chain of list requests and
joining every entity by ID in the browser.

Add narrow read routes with each vertical slice when they are justified by the
operator workflow. Expected candidates are:

- tournament list summaries with lifecycle, participant count, and phase/section
  counts;
- one tournament workspace view with its phases, sections, participants, and
  usable labels;
- one section-operation view with members, rounds, games, round participation
  records, and standings-related links;
- readiness or validation responses that explain the next blocked lifecycle
  action.

Multi-record writes may use dedicated workflow routes when a partial update
would leave an unusable intermediate state. In particular, creating a
tournament with an initial planned structure must be designed as one
transaction if the UI presents it as one action. Do not add generic "save the
whole tournament" endpoints before that need is demonstrated.

### Implementation Sequence

Each step is a complete vertical slice with an operator-visible result and
backend/API contract tests. A later step must not depend on an unverified
earlier contract.

0. **SPA foundation — complete (T24)**
   - Replace the hello-world page with the application shell and responsive
     navigation.
   - Add the shared API client, router, rendering primitives, and status/error
     patterns.
   - Add a frontend smoke path and prove navigation and backend error handling
     without requiring a database for the health check.
1. **Tournament catalog and draft creation — complete (T25)**
   - List tournaments and expose a focused create form for tournament metadata.
   - Add the smallest summary contract needed for the list.
   - Open a tournament overview containing lifecycle and edit state.
2. **Player and tournament registration — complete (T26)**
   - Add reusable player create/edit/list behavior.
   - Register and unregister players for a draft tournament.
   - Display participant names, not only foreign-key IDs.
3. **Draft tournament structure and rules — complete (T27)**
   - Add phases, sections, planned rounds, section membership, and ratings.
   - Add ordered tie-break configuration and make supported versus unsupported
     codes explicit.
   - Add tournament workspace/readiness data so the operator can see what is
     missing before activation.
4. **Activation and section operation — complete (T28)**
   - Surface tournament and section lifecycle actions and their conflict
     messages.
   - Create rounds and manual pairings.
   - Record games, result types, comments, byes, unplayed rounds, absences, and
     awarded scores.
   - Refuse invalid score combinations in the UI and preserve the server's
     authoritative response.
5. **Standings and round review — complete (T29)**
   - Recompute and display section standings after result entry.
   - Show ranks, points, wins/draws/losses, configured tie-break columns, and
     snapshot time.
   - Provide round-by-round navigation and distinguish incomplete games from
     recorded results.
6. **Phase advancement and closeout — complete (T30)**
   - Finish sections and tournaments through explicit transitions.
   - Support manual participant membership in later sections with
     `source_section_id` and `source_rank`.
   - Show final standings and retain a read-only historical workspace.
7. **Usability hardening**
   - Validate dense-table workflows with real tournament-sized data.
   - Review keyboard behavior, responsive layouts, accidental-action
     protection, and repeated operator tasks.
   - Add integration smoke coverage for the complete draft-to-finished path.

### Deferred or Requires a Separate Policy Decision

The following are application behavior, not implied by the current data model:

- Swiss, round-robin, or knockout pairing automation;
- color allocation and repeat-pairing policy;
- automatic phase advancement or placement rules;
- additional tie-break formulas and virtual-opponent policy;
- shared tournament-place rules when a tournament has multiple sections;
- imports, printing/export, authentication, and live multi-operator updates.

The first frontend may support manual pairings and manual advancement. It must
not silently invent defaults for a deferred policy. Pairing automation should
become a separate implementation slice with a documented algorithm and focused
backend tests.

New backend routes are created in tandem with the frontend slice that needs
them. Each route addition must preserve the existing domain services and use a
clearly named read model or command rather than duplicating tournament rules
in JavaScript.
