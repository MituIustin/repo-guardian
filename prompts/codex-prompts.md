# Codex Prompts for Repo Guardian

## How to Use These Prompts

Use one prompt at a time.

Do not ask Codex to implement the entire project in one step.

After each task:

1. review the diff;
2. run tests;
3. run the application;
4. commit the change;
5. update documentation if needed.

## Prompt 1 — Initialize Documentation and Project Awareness

```text
Read AGENTS.md and the documentation in /docs.

This is Repo Guardian, a dissertation project about an AI-assisted DevOps platform for monitoring GitHub Actions builds, diagnosing CI/CD failures, analyzing logs and commits, and generating safe Pull Request proposals.

First task:
Audit the current repository structure and identify:
1. existing frontend structure;
2. where mock data is located;
3. which components can be reused;
4. which components should be rewritten;
5. what is missing for backend integration.

Do not modify files yet.
Return a concise technical audit and a proposed first implementation plan.
```

## Prompt 2 — Frontend Cleanup Plan

```text
Respect AGENTS.md.

Task:
Create a frontend cleanup and redesign plan based on the existing mocked UI.

Requirements:
- all UI text must be in English;
- no emojis;
- identify mock data boundaries;
- propose a feature-based frontend structure;
- propose reusable components;
- propose the first screens to refactor.

Do not implement yet.
Return the plan and list the files that will be modified in the next step.
```

## Prompt 3 — Redesign Frontend Foundation

```text
Respect AGENTS.md and docs/ui-redesign.md.

Task:
Refactor the frontend foundation.

Requirements:
- create or improve the main app layout;
- create reusable components for Button, Card, Badge, EmptyState, LoadingState, ErrorState, PageHeader, and MetricCard;
- keep all text in English;
- remove emojis if any exist;
- keep the code clean and readable;
- do not integrate the backend yet;
- keep mock data separated from production API code.

Before editing, explain the plan and list files that will be touched.
After editing, summarize changes and how to run the frontend.
```

## Prompt 4 — Backend API Foundation

```text
Respect AGENTS.md and docs/backend-plan.md.

Task:
Create the initial backend API foundation.

Requirements:
- health check endpoint;
- PostgreSQL connection;
- environment-based configuration;
- initial entities:
  - User
  - GitHubAccount
  - Repository
  - RepositoryConnection
  - WorkflowRun
  - BuildJob
  - Incident
- database migrations;
- basic endpoints:
  - GET /api/health
  - GET /api/repositories
  - GET /api/incidents
  - GET /api/incidents/{id}
- Docker Compose with PostgreSQL if not already present.

Constraints:
- do not implement GitHub OAuth yet;
- do not implement AI yet;
- do not implement Kubernetes yet;
- do not hardcode secrets.

Before editing, explain the plan and list files that will be touched.
```

## Prompt 5 — Connect Frontend to Backend

```text
Respect AGENTS.md.

Task:
Connect the frontend to the backend API for repositories and incidents.

Requirements:
- create a central API client;
- replace repository mock data with API calls where possible;
- replace incident mock data with API calls where possible;
- keep mock fallback only in a clearly separated development file if needed;
- add loading and error states;
- use English UI text;
- no emojis.

Do not implement GitHub OAuth yet.
```

## Prompt 6 — GitHub OAuth

```text
Respect AGENTS.md and docs/github-integration.md.

Task:
Implement GitHub OAuth login.

Requirements:
- backend login endpoint;
- backend callback endpoint;
- current user endpoint;
- user persistence;
- GitHubAccount persistence;
- frontend login button;
- authenticated app state;
- environment variables for client ID and client secret.

Constraints:
- do not hardcode secrets;
- do not implement repository connection yet;
- do not implement webhooks yet.

Add or update tests where appropriate.
Update docs if the implementation differs from the current plan.
```

## Prompt 7 — Repository Connection

```text
Respect AGENTS.md.

Task:
Implement repository connection after GitHub login.

Requirements:
- list available GitHub repositories;
- connect selected repository;
- store Repository and RepositoryConnection;
- allow selecting monitored branch;
- show connected repositories in the UI.

Constraints:
- do not implement webhooks yet;
- do not implement AI yet;
- keep GitHub API code isolated in a GitHub integration module.
```

## Prompt 8 — GitHub Webhook Processing

```text
Respect AGENTS.md and docs/github-integration.md.

Task:
Implement GitHub webhook processing for workflow_run events.

Requirements:
- POST /api/webhooks/github;
- verify X-Hub-Signature-256;
- deduplicate X-GitHub-Delivery;
- process workflow_run events;
- store WorkflowRun;
- create Incident when conclusion is failure;
- create timeline event;
- add fixtures for success and failure payloads;
- add tests for valid signature, invalid signature, duplicate delivery, and failed workflow incident creation.

Constraints:
- do not download logs yet;
- do not implement AI yet.
```

## Prompt 9 — GitHub Actions Log Download

```text
Respect AGENTS.md.

Task:
Implement GitHub Actions log download for failed workflow runs.

Requirements:
- queue log download after incident creation;
- download logs through GitHub integration module;
- store BuildLog;
- extract LogSections;
- show relevant log sections on the incident detail page;
- add test fixtures for different log types.

Constraints:
- do not implement AI analysis yet;
- keep large logs out of synchronous request-response flows.
```

## Prompt 10 — AI Log Analysis

```text
Respect AGENTS.md and docs/ai-llm-strategy.md.

Task:
Implement AI log analysis with an LLM abstraction layer.

Requirements:
- create LLMProvider interface;
- create MockProvider for tests;
- create first real provider behind the abstraction;
- implement log analysis prompt version log-analysis-v1;
- parse structured JSON output;
- store AIAnalysis;
- store evidence;
- track tokens, latency, provider, model, and estimated cost;
- show AI diagnosis in the incident detail UI.

Constraints:
- business modules must not call provider SDKs directly;
- do not generate Pull Requests yet;
- do not use real LLM calls in automated tests.
```

## Prompt 11 — AI Commit Analysis

```text
Respect AGENTS.md.

Task:
Implement AI commit analysis.

Requirements:
- retrieve commit metadata and diff for the failed workflow run;
- provide relevant diff context to LLMProvider;
- create prompt version commit-analysis-v1;
- store CommitAnalysis or AIAnalysis with type commit_analysis;
- show suspected commit, affected files, confidence, and reasoning in the UI.

Constraints:
- do not generate code changes yet;
- do not create Pull Requests yet.
```

## Prompt 12 — Pull Request Proposal

```text
Respect AGENTS.md.

Task:
Implement Pull Request proposal generation.

Requirements:
- generate a proposed fix using the LLM abstraction layer;
- store PullRequestProposal;
- show generated description and diff in the UI;
- require user approval before PR creation;
- add state transitions:
  - draft
  - ready_for_review
  - approved
  - rejected
  - pr_created
  - failed

Constraints:
- do not create GitHub PRs yet;
- no automatic merge;
- no direct push to default branch.
```

## Prompt 13 — GitHub App Bot PR Creation

```text
Respect AGENTS.md and docs/github-integration.md.

Task:
Implement GitHub App bot Pull Request creation.

Requirements:
- use GitHub App authentication;
- create a new branch;
- commit proposed changes;
- open a Pull Request;
- store PullRequest metadata;
- include diagnosis, evidence, risk level, and verification steps in PR description;
- show PR URL in the UI.

Constraints:
- PR creation requires prior user approval;
- never merge automatically;
- never push to default branch;
- do not hardcode GitHub App secrets.
```

## Prompt 14 — Testing Pass

```text
Respect AGENTS.md and docs/testing-strategy.md.

Task:
Improve test coverage for the current project state.

Focus on:
- webhook signature validation;
- workflow_run payload processing;
- incident creation;
- log parsing;
- LLM response parsing;
- cost calculation;
- Pull Request proposal state transitions.

Do not add unrelated features.
Return a summary of coverage gaps after implementation.
```

## Prompt 15 — Observability

```text
Respect AGENTS.md and docs/observability-plan.md.

Task:
Add basic observability.

Requirements:
- expose Prometheus metrics;
- add metrics for API requests, webhooks, incidents, LLM requests, queue jobs, and PR creation;
- add structured logging for major events;
- add initial Grafana dashboard JSON if appropriate.

Constraints:
- do not expose secrets in logs;
- do not log full raw build logs by default.
```

## Prompt 16 — Kubernetes

```text
Respect AGENTS.md and docs/kubernetes-plan.md.

Task:
Add Kubernetes deployment files.

Requirements:
- frontend deployment and service;
- API deployment and service;
- worker deployment and service if worker exists;
- PostgreSQL or documented external database configuration;
- Redis or RabbitMQ if used;
- ConfigMap;
- secrets.example.yaml;
- liveness and readiness probes;
- HPA for analysis worker;
- README section for running locally with kind or minikube.

Constraints:
- do not commit real secrets;
- keep manifests understandable and dissertation-friendly.
```

## Prompt 17 — Dissertation Documentation Update

```text
Respect AGENTS.md and docs/dissertation-notes.md.

Task:
Update dissertation documentation based on the current implementation.

Create or update:
- docs/architecture.md
- docs/data-model.md
- docs/api-contract.md
- docs/evaluation-plan.md
- docs/dissertation-notes.md

Focus on:
- what has been implemented;
- why the architecture is designed this way;
- current limitations;
- next steps;
- how this supports the dissertation.
```
