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

## Open Questions

These decisions have not been specified and should be settled before the
corresponding behavior is implemented:

- Which tournament format or formats should be supported?
- What blitz time control(s) should a tournament use?
- How should match outcomes be recorded and scored, including draws,
  forfeits, and any tie-break rules?
- How are players added, identified, and assigned to a tournament?
- Should the system support multiple tournaments and retain their results?
- Who will operate the system, and is authentication or access control needed?
- Where will the stack be deployed, and are backup or recovery requirements
  needed?
