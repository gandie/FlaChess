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
