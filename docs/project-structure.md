# Project Structure

## Goal

The repository separates deployable applications, infrastructure, documentation, and cross-application fixtures while keeping the initial system a modular monolith.

## Current Structure

```text
repo-guardian/
  AGENTS.md
  README.md
  .env.example
  apps/
    frontend/
      src/
        api/
        components/
        test/
      Dockerfile
      nginx.conf
      package.json
    api/
      app/
        core/
        health/
        users/
        github_accounts/
        repositories/
        workflow_runs/
        build_jobs/
        incidents/
      alembic/
      tests/
      Dockerfile
      pyproject.toml
  infrastructure/
    docker/
      compose.yaml
    kubernetes/
    prometheus/
    grafana/
  docs/
    decisions/
  tests/
    e2e/
    fixtures/
  prompts/
```

## Application Rules

- Keep backend modules within `apps/api` until extraction has a demonstrated need.
- Keep frontend API access in `src/api` rather than issuing requests throughout components.
- Keep feature-specific tests close to each application.
- Keep cross-application E2E tests and reusable external-system fixtures under root `tests`.
- Keep Docker, future Kubernetes, and observability assets under `infrastructure`.
- Record important technical choices under `docs/decisions`.

## Future Growth

Add frontend feature folders as user-facing workflows are implemented. The backend now includes authentication, GitHub App installation, repository, webhook, build, and log-extraction modules. Add AI analysis, Pull Request automation, notifications, and observability only in roadmap order.

Shared packages should be introduced only after stable API contracts create real duplication. Worker or service directories should not be created before background processing exists and the modular-monolith boundary is proven.

## Mock Data

Temporary last-build data is isolated under `src/mocks` and is never imported by the production API client. Repository identity and connection information comes from the backend. Remove the mock boundary when workflow ingestion is implemented.
