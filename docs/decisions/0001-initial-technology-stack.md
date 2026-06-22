# ADR 0001: Initial Technology Stack

## Status

Accepted

## Context

Repo Guardian needs a maintainable foundation for a dissertation system that will later process GitHub events, build logs, and structured LLM output. The first milestone must remain small while preserving clear boundaries for future domain modules.

## Decision

Use React 19, TypeScript, and Vite for the frontend; FastAPI on Python 3.12 for the backend; SQLAlchemy 2 with asynchronous sessions and asyncpg; Alembic for migrations; PostgreSQL 17; Docker Compose; and Nginx for the containerized frontend and API proxy.

The backend will be deployed as one modular-monolith process. Modules are organized by domain feature but share configuration, database infrastructure, and one PostgreSQL database.

The first migration contains users, GitHub accounts, repositories, workflow runs, build jobs, and incidents. It does not contain OAuth credentials or advanced analysis and automation entities.

## Rationale

FastAPI keeps future log-processing and AI-oriented Python code close to the application layer while providing typed request validation and generated OpenAPI documentation. SQLAlchemy and Alembic make persistence and schema changes explicit enough to discuss and demonstrate during a dissertation defense.

React and Vite provide a focused frontend foundation without introducing server-side rendering or a full-stack frontend framework before it is needed. Docker Compose gives each developer the same PostgreSQL, migration, API, and frontend topology.

## Consequences

- Python and TypeScript are both required for local development.
- Long-running work must later move behind background-job interfaces rather than run inside API requests.
- Module boundaries must be maintained inside the monolith before service extraction is considered.
- PostgreSQL-specific UUID support is accepted because PostgreSQL is the selected production database.
- A separate repository-connection entity will be introduced when repository authorization is implemented.

