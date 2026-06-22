# Roadmap

## Roadmap Philosophy

The project must be built incrementally. The goal is not to implement the most complex features first, but to reach a working end-to-end flow early and then improve it.

Correct order:

1. Stabilize project structure.
2. Improve the mocked frontend.
3. Add backend API.
4. Add GitHub authentication.
5. Connect repositories.
6. Process webhooks.
7. Persist workflow runs and incidents.
8. Download logs.
9. Analyze logs with AI.
10. Analyze commits with AI.
11. Generate Pull Request proposals.
12. Add tests.
13. Add LLM provider abstraction.
14. Add cost tracking.
15. Add notifications.
16. Add observability.
17. Split selected modules into services.
18. Add Kubernetes.
19. Evaluate models.
20. Write and polish the dissertation.

## Phase 0 — Project Foundation

Implementation status: completed for the initial application scaffold. The repository now contains the frontend, backend, PostgreSQL migration, health checks, Docker Compose environment, tests, and setup documentation.

### Goals

- Add project-level instructions.
- Add documentation.
- Review existing frontend prototype.
- Identify mock data boundaries.
- Prepare for backend integration.

### Deliverables

- `AGENTS.md`
- `/docs` folder
- cleaned project structure
- initial technical decisions
- frontend audit

### Completion Criteria

The project has clear instructions, documentation, and a stable plan for incremental development.

## Phase 1 — Frontend Redesign Foundation

### Goals

- Improve the existing mock UI.
- Define layout, navigation, design language, and reusable components.
- Prepare UI screens for real backend data.

### Deliverables

- redesigned dashboard;
- improved repository list;
- improved incidents page;
- improved build details page;
- improved AI diagnosis panel;
- improved Pull Request proposal flow;
- empty states, loading states, and error states.

Implementation status: the dashboard shell, authentication-aware states, primary navigation, and repository management screen are implemented. Build and incident screens remain intentionally empty until their backend flows exist.

### Completion Criteria

The frontend looks credible as a developer tool and no longer feels like a superficial mockup.

## Phase 2 — Backend API Foundation

Implementation status: foundation in progress. The API, PostgreSQL integration, first six domain entities, migrations, and health endpoints are implemented. Repository and incident read endpoints remain deferred until their application behavior is introduced.

### Goals

- Add a real backend API.
- Add database persistence.
- Define initial entities.

### Deliverables

- backend API;
- PostgreSQL integration;
- database migrations;
- health check;
- basic repository and incident endpoints;
- Docker Compose.

### Completion Criteria

The frontend can read basic data from the backend instead of relying only on local mock data.

## Phase 3 — GitHub OAuth and Repository Connection

Implementation status: completed. GitHub OAuth, encrypted token persistence, repository discovery, monitored-branch validation, and user repository connections are implemented.

### Goals

- Authenticate users with GitHub.
- Allow users to connect repositories.

### Deliverables

- GitHub OAuth flow;
- user persistence;
- GitHub account persistence;
- repository listing;
- repository connection flow.

### Completion Criteria

A real user can log in with GitHub and connect at least one repository.

## Phase 4 — Webhook Processing

### Goals

- Receive GitHub workflow events.
- Create incidents for failed builds.

Implementation status: signed `workflow_run` ingestion, delivery deduplication, multi-installation GitHub source management, repository synchronization and exclusions, short-lived installation credentials, confirmed workflow and job reruns, monitored-branch workflow and job persistence, failed-run incident creation, log download, deterministic error excerpt extraction, and real-time build and repository WebSocket updates are implemented.

The current UI groups runs by repository, emphasizes the latest run, and expands stored jobs, structured steps, error evidence, and rerun actions on demand.

### Deliverables

- webhook endpoint;
- signature verification;
- `workflow_run` event support;
- workflow run persistence;
- incident creation;
- duplicate delivery handling.

### Completion Criteria

A failed GitHub Actions workflow creates an incident in Repo Guardian.

## Phase 5 — GitHub Actions Log Download

### Goals

- Download and parse logs for failed builds.

### Deliverables

- background job for log download;
- log storage;
- log parser;
- relevant section extraction;
- UI for log sections.

### Completion Criteria

An incident page displays relevant failed build logs.

## Phase 6 — AI Log Analysis

### Goals

- Generate structured AI diagnosis for logs.

### Deliverables

- LLM abstraction skeleton;
- mock provider;
- first real provider;
- log analysis prompt;
- structured JSON output;
- error classification;
- confidence score;
- evidence lines.

### Completion Criteria

The incident page shows an AI diagnosis based on real logs.

## Phase 7 — AI Commit Analysis

### Goals

- Connect log errors to recent code changes.

### Deliverables

- commit metadata retrieval;
- diff retrieval;
- suspicious commit detection;
- root cause explanation;
- affected files;
- risk level.

### Completion Criteria

Repo Guardian can explain which commit likely caused the failure and why.

## Phase 8 — Pull Request Proposal and GitHub App Bot

### Goals

- Generate safe PR proposals.
- Create PRs after user approval.

### Deliverables

- add Contents and Pull requests write permissions only when Pull Request automation is implemented;
- branch creation;
- file modification;
- commit creation;
- Pull Request creation;
- PR description template;
- approval step in UI.

### Completion Criteria

A user can approve a generated fix and Repo Guardian opens a Pull Request.

## Phase 9 — Testing

### Goals

- Build a serious test suite.

### Deliverables

- unit tests;
- integration tests;
- E2E tests;
- GitHub payload fixtures;
- build log fixtures;
- mock LLM provider;
- mock GitHub client.

### Completion Criteria

The core workflow is covered by automated tests.

## Phase 10 — LLM Provider Abstraction and Cost Tracking

### Goals

- Support multiple model providers.
- Track cost and performance.

### Deliverables

- provider interface;
- OpenAI provider;
- Anthropic or Gemini provider;
- local/mock provider;
- token usage tracking;
- latency tracking;
- estimated cost tracking;
- provider comparison storage.

### Completion Criteria

The user can select a model and the system tracks cost and latency.

## Phase 11 — Notifications

### Goals

- Inform users about important events.

### Deliverables

- in-app notification center;
- notification events;
- email notification support;
- notification preferences.

### Completion Criteria

Users are notified when analysis completes or PR proposals are ready.

## Phase 12 — Observability

### Goals

- Make the system measurable and demonstrable.

### Deliverables

- Prometheus metrics;
- Grafana dashboards;
- structured logs;
- queue metrics;
- LLM metrics;
- GitHub API metrics.

### Completion Criteria

System health, incidents, AI cost, queue state, and API activity are visible in dashboards.

## Phase 13 — Microservice Extraction

### Goals

- Extract selected modules if the monolith is stable.

### Candidate Services

- API Service
- Webhook Service
- Analysis Worker
- LLM Gateway
- PR Automation Service
- Notification Service

### Completion Criteria

At least one or two services are clearly separated and communicate through HTTP or a queue.

## Phase 14 — Kubernetes

### Goals

- Demonstrate scalable deployment.

### Deliverables

- Kubernetes manifests;
- deployments;
- services;
- config maps;
- secrets;
- probes;
- HPA for workers;
- Prometheus/Grafana in cluster.

### Completion Criteria

The system can run in a local Kubernetes cluster and demonstrate scaling of analysis workers.

## Phase 15 — Evaluation and Dissertation

### Goals

- Prepare the academic contribution.

### Deliverables

- model comparison dataset;
- evaluation metrics;
- charts;
- architecture diagrams;
- final dissertation chapters;
- limitations and future work.

### Completion Criteria

The project is ready for demonstration and dissertation writing.
