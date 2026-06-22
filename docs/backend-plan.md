# Backend Plan

## Goal

Build a backend API that supports GitHub integration, CI/CD monitoring, incident persistence, AI analysis, Pull Request automation, testing, observability, and future microservice extraction.

## Recommended Backend Options

Possible stacks:

- ASP.NET Core Web API;
- NestJS;
- FastAPI.

If the existing project or developer preference favors .NET, ASP.NET Core is a strong option.

## Initial Backend Responsibilities

The first backend version should support:

- health check;
- user model;
- repository model;
- workflow run model;
- incident model;
- database migrations;
- simple API endpoints;
- Docker Compose with PostgreSQL.

Do not implement AI or Kubernetes in the first backend task.

## Recommended Module Structure

```text
apps/api/
  src/
    Auth/
    Repositories/
    GitHub/
    Webhooks/
    WorkflowRuns/
    Incidents/
    Logs/
    AI/
    PullRequests/
    Notifications/
    Observability/
    Shared/
```

For .NET, this could be adapted to:

```text
Controllers/
Application/
Domain/
Infrastructure/
Modules/
```

## Backend Development Order

### Step 1 — Foundation

Deliverables:

- API project;
- health endpoint;
- database connection;
- migration setup;
- environment configuration;
- error handling middleware.

### Step 2 — Data Model

Implement:

- User;
- GitHubAccount;
- Repository;
- RepositoryConnection;
- WorkflowRun;
- BuildJob;
- Incident.

### Step 3 — Read API

Implement:

- list repositories;
- repository details;
- list workflow runs;
- list incidents;
- incident details.

### Step 4 — GitHub OAuth

Implement:

- GitHub login;
- callback;
- token handling;
- current user endpoint.

### Step 5 — Repository Connection

Implement:

- list available GitHub repositories;
- connect repository;
- disconnect repository;
- update monitored branch.

### Step 6 — Webhooks

Implement:

- GitHub webhook endpoint;
- signature verification;
- delivery deduplication;
- workflow run processing;
- incident creation.

### Step 7 — Background Jobs

Implement queue-based processing for:

- log download;
- log parsing;
- AI analysis;
- PR proposal generation;
- notifications.

### Step 8 — GitHub Actions Logs

Implement:

- download logs;
- store logs;
- parse logs;
- extract relevant sections.

### Step 9 — AI Analysis

Implement:

- LLM abstraction;
- mock provider;
- real provider;
- structured diagnosis;
- cost tracking.

### Step 10 — Pull Request Automation

Implement:

- GitHub App authentication;
- branch creation;
- file updates;
- commit;
- Pull Request creation.

## Backend Rules

- Use English names.
- Do not use emojis.
- Avoid hardcoded secrets.
- Validate external payloads.
- Verify webhook signatures.
- Add tests for business logic.
- Do not mix GitHub API code into controllers directly.
- Do not call LLM provider SDKs directly from controllers.
- Use application services.
- Keep controllers thin.

## Error Handling

Create consistent error responses:

```json
{
  "error": {
    "code": "GITHUB_API_ERROR",
    "message": "GitHub API request failed.",
    "details": []
  }
}
```

Common error codes:

```text
VALIDATION_ERROR
UNAUTHORIZED
FORBIDDEN
NOT_FOUND
GITHUB_API_ERROR
GITHUB_WEBHOOK_SIGNATURE_INVALID
LLM_PROVIDER_ERROR
LOG_DOWNLOAD_FAILED
PR_CREATION_FAILED
INTERNAL_ERROR
```

## Configuration

Use environment variables for:

```text
DATABASE_URL
GITHUB_CLIENT_ID
GITHUB_CLIENT_SECRET
GITHUB_WEBHOOK_SECRET
GITHUB_APP_ID
GITHUB_APP_SLUG
GITHUB_APP_PRIVATE_KEY_BASE64
OPENAI_API_KEY
ANTHROPIC_API_KEY
GEMINI_API_KEY
REDIS_URL
RABBITMQ_URL
```

## Background Processing

Use background workers for:

- downloading logs;
- parsing logs;
- running LLM analysis;
- generating fix proposals;
- sending notifications.

Do not perform long-running work inside request-response flows.

## Testing

Backend tests should cover:

- entity validation;
- webhook signature verification;
- webhook payload mapping;
- workflow run persistence;
- incident creation;
- log parsing;
- LLM response parsing;
- cost calculation;
- PR proposal state transitions.
