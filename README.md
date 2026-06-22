# Repo Guardian

Repo Guardian is an AI-assisted DevOps platform for investigating failed GitHub Actions workflows. The project is being developed as a dissertation system with an emphasis on explainable incident analysis, human-approved remediation, testability, and security-aware integrations.

This repository contains the application foundation, GitHub OAuth login, repository connections, signed GitHub webhook ingestion, real-time build monitoring, bounded failure-log extraction, and incident creation. AI analysis remains deferred.

## Technology Stack

- React 19, TypeScript, and Vite
- FastAPI on Python 3.12
- SQLAlchemy 2 with asyncpg
- Alembic migrations
- PostgreSQL 17
- Docker Compose and Nginx

The backend is a modular monolith. Feature modules share one API process and database while retaining explicit boundaries for future development.

## Repository Structure

```text
apps/
  api/          FastAPI application, models, migrations, and tests
  frontend/     React application and frontend tests
docs/           Architecture and dissertation documentation
infrastructure/
  docker/       Local Docker Compose environment
tests/          Cross-application fixtures and future E2E tests
```

## Initial Database Schema

The first migration creates only the foundation entities:

- `users`
- `github_accounts`
- `repositories`
- `workflow_runs`
- `build_jobs`
- `incidents`

Build logs, AI analyses, Pull Request proposals, notifications, and cost records are not part of this milestone.

Migration `0002` adds encrypted OAuth credential fields to `github_accounts`. Tokens are never stored as plain text.

Migration `0003` adds `repository_connections`, which stores each user's selected monitoring branch.

Migration `0004` adds webhook delivery deduplication, repository webhook health, and redacted build-log excerpts.

Migration `0005` adds GitHub App installations, allowing one installation to synchronize and monitor many repositories.

Migration `0006` adds installation monitoring state so synchronized sources can be disconnected and deliberately reconnected without a later webhook silently restoring them.

Migration `0007` stores structured GitHub Actions step metadata on each build job for expandable build investigation views.

## Configure the GitHub App

Repo Guardian uses a GitHub App for automatic repository synchronization, workflow webhooks, and short-lived installation credentials. One installation covers all selected repositories in a GitHub user account or organization.

First, expose the local frontend through an HTTPS tunnel because GitHub cannot deliver webhooks to `localhost`:

```powershell
cloudflared tunnel --url http://localhost:8080
```

Keep that terminal open and copy the generated `https://...trycloudflare.com` URL. Then create a GitHub App under `GitHub Settings > Developer settings > GitHub Apps > New GitHub App` with:

```text
Homepage URL: http://localhost:8080
Setup URL: http://localhost:8000/api/github-app/setup
Webhook URL: https://your-tunnel.trycloudflare.com/api/webhooks/github
Webhook secret: the value of GITHUB_WEBHOOK_SECRET
Repository permission: Actions (Read and write)
Repository permission: Metadata (Read-only)
Subscribe to events: Workflow run
```

Generate a private key on the GitHub App settings page. Record the numeric App ID and the app slug from `github.com/apps/<app-slug>`. Convert the downloaded PEM file into one base64 line with Windows PowerShell:

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("C:\path\to\your-app.private-key.pem"))
```

Add these values to `.env` without quotes:

```text
GITHUB_APP_ID=123456
GITHUB_APP_SLUG=your-app-slug
GITHUB_APP_PRIVATE_KEY_BASE64=the-base64-private-key
GITHUB_WEBHOOK_SECRET=the-same-secret-configured-in-github
```

Recreate the services, open `http://localhost:8080/repositories`, and select `Install GitHub App`. Choose a GitHub account or organization and either all repositories or selected repositories. Existing Repo Guardian connections are matched by GitHub repository ID and keep their monitored branch; newly synchronized repositories initially monitor their default branch.

Install the app once for each GitHub organization that should be monitored. If the app is installed for all repositories, repositories created later are synchronized automatically. Old manually created repository webhooks can be removed after the GitHub App is working to prevent duplicate deliveries.

The repository page lists every linked personal account or organization. Each source can be synchronized, managed in GitHub, or disconnected independently. `Disconnect all` pauses monitoring for every source while retaining installation metadata for an explicit later reconnection. Repository and installation webhooks refresh the page through an authenticated WebSocket.

`Disconnect repositories` is reversible and leaves the GitHub App installed. `Disconnect account` is destructive: after confirmation, Repo Guardian uninstalls the GitHub App and deactivates its repository connections. The manual connection flow asks for a GitHub source first, then limits repository and branch choices to that source.

The Builds page can request a complete workflow rerun, a failed-jobs rerun, or an individual job rerun. These are explicit user actions and require the GitHub App `Actions: Read and write` permission. If the App was initially installed with read-only Actions access, update the permission in the GitHub App settings and approve the permission change for each existing installation.

Builds are grouped by repository with the owner and repository name shown separately. The latest matching run is shown first; previous runs, jobs, steps, extracted failure evidence, GitHub links, and rerun actions are progressively disclosed.

## Run with Docker Compose

Prerequisites:

- Docker with Docker Compose

Create the local environment file:

```powershell
Copy-Item .env.example .env
```

Replace the example database password in `.env`, including the password embedded in `DATABASE_URL`. Then start the services:

```powershell
docker compose --env-file .env -f infrastructure/docker/compose.yaml up --build
```

The application can run without GitHub credentials, but login and GitHub App installation remain unavailable until their respective configuration is provided.

## Configure GitHub OAuth

Create a GitHub OAuth App with these local development values:

```text
Homepage URL: http://localhost:8080
Authorization callback URL: http://localhost:8000/api/auth/github/callback
```

Add the generated client ID and client secret to `.env`:

```text
GITHUB_CLIENT_ID=your-client-id
GITHUB_CLIENT_SECRET=your-client-secret
```

Generate a token-encryption key:

```powershell
docker run --rm repo-guardian-api python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Generate a persistent session-signing secret:

```powershell
docker run --rm repo-guardian-api python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Copy the generated values into `TOKEN_ENCRYPTION_KEY` and `SESSION_SECRET` in `.env`, then recreate the API and frontend:

```powershell
docker compose --env-file .env -f infrastructure/docker/compose.yaml up --build --detach
```

Open `http://localhost:8080` and select `Continue with GitHub`.

The services are available at:

- Frontend: `http://localhost:8080`
- API health: `http://localhost:8000/api/health`
- API readiness: `http://localhost:8000/api/ready`
- OpenAPI documentation: `http://localhost:8000/api/docs`

Stop the services with:

```powershell
docker compose --env-file .env -f infrastructure/docker/compose.yaml down
```

Add `--volumes` only when the local PostgreSQL data should also be removed.

## Run Applications Separately

Backend prerequisites:

- Python 3.12
- A running PostgreSQL 17 database

From `apps/api`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
$env:DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/repo_guardian"
$env:FRONTEND_ORIGINS = '["http://localhost:5173"]'
alembic upgrade head
uvicorn app.main:app --reload
```

Frontend prerequisites:

- Node.js 22
- npm 10

From `apps/frontend`:

```powershell
npm install
npm run dev
```

Vite proxies `/api` requests to `http://localhost:8000` during local development.

## Tests and Checks

Backend:

```powershell
cd apps/api
ruff check .
pytest
```

The migration integration test requires a dedicated PostgreSQL database and a `TEST_DATABASE_URL` environment variable. It upgrades and then downgrades that database.

Frontend:

```powershell
cd apps/frontend
npm run lint
npm run typecheck
npm test
npm run build
```

Automated tests do not call GitHub or LLM providers.

## Current Boundaries

The current milestone does not implement AI analysis, Pull Request automation, queues, notifications, Prometheus, Grafana, Kubernetes, or microservices. Error extraction is deterministic evidence collection, not AI diagnosis. These capabilities are sequenced in [docs/roadmap.md](docs/roadmap.md).

If you authenticated before repository management was added, sign out and authorize GitHub again. Repository discovery requires the new OAuth `repo` scope, including for private repositories.
