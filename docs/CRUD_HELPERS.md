# FastAPI CRUD and Form Helpers

Status: FastCRUD and SQLAdmin are adopted for the Player entity. FastCRUD owns
the `/api/players` routes; SQLAdmin owns the internal `/admin` interface.

This document evaluates helpers for the Fla Chess stack: FastAPI, async SQLAlchemy
2 mapped classes, asyncpg/PostgreSQL, Alembic, Pydantic, and a plain static HTML
frontend served by FastAPI.

## Recommendation

Use **FastCRUD** as the primary runtime library for entity CRUD routes. It directly
supports async SQLAlchemy 2 and can generate CRUD routers from SQLAlchemy models
plus Pydantic create/update schemas. Keep custom FastAPI routes for domain-specific
operations. It fits the existing `AsyncSession` session dependency and avoids a
second database/session abstraction.

Use **SQLAdmin** for an internal administration UI. It supports FastAPI,
async SQLAlchemy engines, and WTForms-generated CRUD forms. It is more appropriate
than an application-wide frontend generator because it does not replace the plain
HTML frontend or generate public APIs.

Use a code generator only as scaffolding, not as a runtime dependency:

- Prefer a small project-local generator or an established full-stack scaffold
  that emits the project's existing SQLAlchemy models, Pydantic schemas,
  Alembic migrations, and FastAPI routers.
- Do not adopt fsgenerator or a scaffold that generates a separate architecture
  (for example SQLite/Jinja2 templates) as the first implementation.
- For entities that need a public HTML experience, let the project build explicit
  HTMX or static-JavaScript forms over the FastCRUD API instead of assuming an
  admin UI is the public frontend.

## Runtime API helpers

### FastCRUD

[FastCRUD](https://benavlabs.github.io/fastcrud/) provides:

- async CRUD operations;
- automatic `crud_router` endpoint creation;
- SQLAlchemy 2 and optional SQLModel support;
- Pydantic 2 schemas;
- filtering, sorting, offset/cursor pagination, and joins.

Its documented [PyPI release](https://pypi.org/project/fastcrud/) is 0.23.0,
released October 11, 2026. The package is MIT-licensed and requires Python 3.10
or newer. The project is actively maintained and has a public test suite.

Fit:

- High for the existing Player model.
- Requires separate create and update Pydantic schemas, which is desirable API
  validation but not entirely schema-free.
- Uses async SQLAlchemy patterns compatible with the existing `AsyncSession`.

Sources:

- https://benavlabs.github.io/fastcrud/
- https://github.com/benavlabs/fastcrud
- https://pypi.org/project/fastcrud/

### FastAPI SQLAlchemy Toolkit

[fastapi-sqlalchemy-toolkit](https://pypi.org/project/fastapi-sqlalchemy-toolkit/)
is an async SQLAlchemy toolkit with CRUD methods, filtering, ordering, foreign-key
existence checks, unique constraints, and many-to-many support.

Its latest listed package is 0.8.4, released September 29, 2026, and it requires
Python 3.11 or newer. It is useful when the application wants to retain handwritten
routers but remove database boilerplate.

Fit:

- Medium. It is more of a repository/data-access helper than an automatic route
  generator.
- A strong fallback if FastCRUD's router conventions are too opinionated.
- The documentation is partly Russian, and the ecosystem/community is smaller
  than SQLAdmin or FastCRUD.

Sources:

- https://pypi.org/project/fastapi-sqlalchemy-toolkit/
- https://github.com/e-kondr01/fastapi-sqlalchemy-toolkit

### fastapi-crudrouter and v2 fork

[fastapi-crudrouter-v2](https://pypi.org/project/fastapi-crudrouter-v2/) exposes
memory, SQLAlchemy, async, Gino, Ormar, and Tortoise backends and can generate
documented CRUD routes.

The v2 package is listed at 0.1.6, released June 17, 2026. The upstream project
is older and is primarily designed around Pydantic models or backend-specific
adapters rather than the project's SQLAlchemy 2 async session pattern.

Fit:

- Low to medium. It may generate routes quickly, but it has less direct alignment
  with native async `AsyncSession` than FastCRUD.
- Verify an exact SQLAlchemy 2/asyncpg integration in a focused prototype before
  adopting it.

Sources:

- https://pypi.org/project/fastapi-crudrouter-v2/
- https://github.com/awtkns/fastapi-crudrouter

## Internal administration/form helpers

### SQLAdmin

[SQLAdmin](https://github.com/smithyhq/sqladmin) is a FastAPI/Starlette
administration interface for SQLAlchemy models. It supports:

- sync and async SQLAlchemy engines;
- FastAPI integration;
- WTForms-generated create/edit forms;
- SQLModel;
- Tabler-based UI;
- search, sorting, list/detail views, and authentication hooks.

The documented latest package is 0.32.0, released September 20, 2026.

Fit:

- High for an internal `/admin` interface.
- Low for public application forms: it is an admin panel, not a public frontend.
- Add it only after authentication and authorization requirements are decided.
  SQLAdmin provides integration hooks, not a complete application policy.

Sources:

- https://github.com/smithyhq/sqladmin
- https://pypi.org/project/sqladmin/

### CRUDAdmin

[CRUDAdmin](https://benavlabs.github.io/crudadmin/) combines FastCRUD and HTMX
to generate an authenticated admin UI directly from SQLAlchemy models and Pydantic
schemas.

The package is 0.6.0, released October 8, 2026. It provides authentication,
CSRF protection, event tracking, search/filtering, and session backends.

Fit:

- Medium to high for a feature-rich internal admin panel.
- Lower confidence for new projects than SQLAdmin because it explicitly labels
  itself experimental and its API may change between releases.
- It is a strong best-fit if the team wants HTMX, built-in auth, and audit
  features rather than WTForms and a Tabler UI.

Sources:

- https://benavlabs.github.io/crudadmin/
- https://github.com/benavlabs/crudadmin
- https://pypi.org/project/crudadmin/

## Code generation and scaffolding

### FastAPI-Forge

[FastAPI-Forge](https://github.com/mslaursen/fastapi-forge) generates SQLAlchemy
models, Pydantic schemas, REST CRUD endpoints, DAOs, tests, and Docker Compose
configuration from a project definition or existing database connection.

Fit:

- Medium as a whole-project or database-to-project generator.
- Verify generated conventions and migrations against the current async session
  and package layout before using it for existing Fla Chess code.
- It is better for bootstrapping a conventional project than for incremental
  entity additions.

Source:

- https://github.com/mslaursen/fastapi-forge

### fsgenerator

[fsgenerator](https://pypi.org/project/fsgenerator/) generates a complete
FastAPI/SQLAlchemy/Jinja2 application from JSON entity definitions. It includes
models, Pydantic schemas, repository implementations, routes, frontend views,
and entity relations.

Fit:

- Low for this project. It is a complete-application generator, and package
  metadata indicates SQLite-oriented defaults and Jinja2 rather than the existing
  async PostgreSQL/static architecture.
- It can be useful as a reference for entity metadata and relation handling,
  but should not overwrite or replace the current application.

Sources:

- https://pypi.org/project/fsgenerator/
- https://github.com/SINENSIA/fastapi-sqlachemy-jinja2

### Fastisan

[Fastisan](https://pypi.org/project/fastisan/) is a CLI that generates models,
Pydantic schemas, repositories, services, routers, middleware, and CRUD resources
for FastAPI/SQLAlchemy projects.

Its listed release is 0.1.1, released October 26, 2026. It targets async
SQLAlchemy and PostgreSQL/asyncpg, which is technically close to the project.

Fit:

- Medium, but treat it as experimental until conventions and output diffs are
  validated against Alembic and the current modular package layout.
- It is not a frontend-form generator.

Source:

- https://pypi.org/project/fastisan/

## Suggested Player adoption sequence

1. Add `PlayerCreate` and `PlayerUpdate` Pydantic models.
2. Add a FastCRUD router for `/api/players`, while preserving FastAPI's existing
   `/api/health` route and router composition.
3. Use the existing `app.database.get_session` dependency through FastCRUD's
   session callable/configuration, rather than creating a second engine/session
   system.
4. Decide whether `/players` is a public static application or only a protected
   administration section.
5. If it is only administration, mount SQLAdmin and add `PlayerAdmin` after the
   authentication decision.
6. Add a local `make`-style or Python entity scaffold only after at least two
   entities share the same CRUD structure; until then, FastCRUD plus explicit
   Pydantic schemas has enough reuse without locking in an experimental generator.

## Final decision

- **FastCRUD:** first choice for runtime API CRUD.
- **SQLAdmin:** first choice for a mature internal admin/form UI.
- **CRUDAdmin:** evaluate in a prototype if HTMX, built-in security, and audit
  logging are more important than API stability.
- **fastapi-sqlalchemy-toolkit:** second choice if the project wants handwritten
  routes and only database-layer reuse.
- **fastapi-crudrouter-v2:** not the first choice for this async SQLAlchemy 2
  stack without a focused compatibility prototype.
- **Full-project generators:** not recommended for current incremental work;
  they should scaffold new modules or new projects rather than rewrite this one.
