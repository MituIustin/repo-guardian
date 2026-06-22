# Architecture

## Architecture Goal

Repo Guardian should start as a modular monolith and evolve toward selected microservices only after the end-to-end workflow is stable.

This avoids premature complexity while still supporting a strong dissertation architecture.

## Implemented Foundation

The current implementation uses a React frontend, a FastAPI modular monolith, asynchronous SQLAlchemy sessions, and PostgreSQL. Docker Compose starts PostgreSQL, applies Alembic migrations, starts the API after migration success, and starts the Nginx-served frontend after API readiness succeeds.

The backend currently contains modules for authentication, GitHub OAuth, GitHub App installations, repository management, signed webhook processing, builds, bounded log extraction, incidents, and health checks. They are internal module boundaries inside one deployable application, not microservices.

GitHub OAuth uses a signed, HTTP-only session cookie. The GitHub integration module owns provider HTTP calls, while the authentication module owns OAuth state validation, encrypted token persistence, and current-user session behavior.

Health behavior is separated deliberately:

- `/api/health` reports process liveness without querying PostgreSQL;
- `/api/ready` verifies PostgreSQL connectivity before reporting readiness.

The GitHub App setup flow synchronizes selected repositories into the same domain model as OAuth repository connections. Multiple personal or organization installations may belong to one Repo Guardian user, while OAuth remains the login identity. Webhook processing and user-requested reruns exchange an app JWT for a short-lived installation token when a connection has an installation ID. The webhook endpoint commits state before in-process, user-scoped build and repository WebSocket hubs publish updates. REST provides initial state and reconnect recovery. These hubs are intentionally process-local while Compose runs one API worker; a shared event transport is required before horizontal API scaling. Queues, LLM providers, and observability components remain planned.

Repository discovery and branch validation are credential-source aware: OAuth is used for the login account, while installation tokens are used for repositories selected from another personal account or organization. Build jobs persist structured step metadata for progressive UI disclosure; raw log evidence remains in the bounded log-excerpt module.

## Initial Architecture

```text
Frontend
   |
Backend API
   |
PostgreSQL
   |
Queue
   |
Background Worker
   |
GitHub API / GitHub Webhooks
   |
LLM Provider Layer
```

## Future Architecture

```text
Frontend
   |
API Gateway / Backend API
   |
-------------------------------------------------
| Auth Service                                  |
| Repository Service                            |
| Webhook Service                               |
| CI Monitoring Service                         |
| Incident Service                              |
| Analysis Worker                               |
| LLM Gateway                                   |
| PR Automation Service                         |
| Notification Service                          |
-------------------------------------------------
   |
PostgreSQL / Redis / RabbitMQ
   |
Prometheus / Grafana
```

## Recommended Initial Modules

### Auth Module

Responsibilities:

- GitHub OAuth login;
- user sessions;
- current user endpoint;
- user persistence;
- GitHub account association.

### Repository Management Module

Responsibilities:

- list repositories;
- connect repositories;
- store repository metadata;
- manage monitored branch;
- show repository status.

### GitHub Integration Module

Responsibilities:

- GitHub API client;
- GitHub App JWT creation and installation-token exchange;
- installation repository synchronization;
- GitHub OAuth integration;
- repository metadata retrieval;
- workflow run retrieval;
- log download;
- commit and diff retrieval;
- PR creation.

### Webhook Processing Module

Responsibilities:

- receive GitHub webhook events;
- verify webhook signatures;
- deduplicate deliveries;
- route events to internal handlers;
- publish internal domain events.

### CI Monitoring Module

Responsibilities:

- store workflow runs;
- store build jobs;
- detect failed builds;
- create incidents from failed workflows.

### Incident Management Module

Responsibilities:

- incident lifecycle;
- severity;
- category;
- status;
- timeline events;
- incident detail pages.

### Log Processing Module

Responsibilities:

- store raw logs;
- extract relevant sections;
- detect failed step;
- detect error lines;
- normalize logs for AI input.

### AI Analysis Module

Responsibilities:

- build prompts;
- request LLM analysis;
- validate structured responses;
- store AI diagnosis;
- classify errors;
- assign confidence score.

### LLM Provider Module

Responsibilities:

- provider abstraction;
- provider configuration;
- model selection;
- cost tracking;
- latency tracking;
- prompt versioning;
- response validation.

### Pull Request Automation Module

Responsibilities:

- generate PR proposal;
- create branch;
- apply patch;
- commit changes;
- create Pull Request;
- store PR metadata;
- enforce human approval.

### Notification Module

Responsibilities:

- in-app notifications;
- email notifications;
- notification preferences;
- event-based notifications.

### Observability Module

Responsibilities:

- metrics;
- logs;
- traces if added later;
- health checks;
- readiness checks;
- dashboards.

## Internal Event Flow

Important internal events:

```text
RepositoryConnected
WebhookReceived
WorkflowRunCompleted
WorkflowRunFailed
IncidentCreated
LogsDownloadRequested
LogsDownloaded
LogsParsed
AIAnalysisRequested
AIAnalysisCompleted
CommitAnalysisCompleted
PRProposalGenerated
PullRequestCreated
NotificationSent
```

## Core Workflow

```text
GitHub workflow_run webhook
        |
Webhook Processing Module
        |
CI Monitoring Module
        |
Incident Management Module
        |
Log Processing Module
        |
AI Analysis Module
        |
Pull Request Automation Module
        |
Notification Module
```

## Data Flow for Failed Build

1. GitHub sends `workflow_run` payload.
2. Webhook module verifies signature.
3. System stores event metadata.
4. CI module stores workflow run.
5. Incident module creates incident if the workflow failed.
6. Log processing job is queued.
7. Worker downloads logs from GitHub.
8. Log parser extracts relevant error sections.
9. AI module analyzes logs.
10. Commit analysis correlates log failure with diffs.
11. PR proposal is generated.
12. User approves PR creation.
13. GitHub App bot opens Pull Request.

## Why Modular Monolith First

A modular monolith is recommended initially because:

- the project will evolve quickly;
- domain boundaries are not fully proven yet;
- debugging is easier;
- deployment is simpler;
- tests are easier to write;
- microservices can be extracted later based on real boundaries.

## When to Extract Microservices

Extract services only when:

- the module has clear responsibilities;
- it has independent scaling needs;
- it communicates through stable contracts;
- it is covered by tests;
- the end-to-end workflow already works.

Best candidates:

1. Analysis Worker
2. LLM Gateway
3. Webhook Service
4. Notification Service
5. PR Automation Service

## Deployment Evolution

### Stage 1

Local development with frontend, backend, PostgreSQL.

### Stage 2

Docker Compose with backend, frontend, PostgreSQL, Redis or RabbitMQ.

### Stage 3

Separate worker for log processing and AI analysis.

### Stage 4

Kubernetes deployment with service separation.

### Stage 5

Prometheus and Grafana observability.

## Architectural Risks

### Risk: Too Many Services Too Early

Mitigation:

- start with modular monolith;
- extract only stable modules.

### Risk: AI Output Is Unreliable

Mitigation:

- use structured output;
- validate JSON;
- require evidence;
- show confidence and uncertainty;
- require user approval for PR creation.

### Risk: GitHub API Rate Limits

Mitigation:

- cache data;
- avoid unnecessary calls;
- process heavy tasks in queues;
- implement retries and backoff.

### Risk: Sensitive Data in Logs

Mitigation:

- redact secrets;
- avoid exposing full logs when unnecessary;
- mark sensitive sections;
- store access-controlled logs.

### Risk: Expensive LLM Usage

Mitigation:

- truncate logs intelligently;
- extract relevant sections;
- track tokens and cost;
- support cheaper or local models;
- use mock providers in tests.
