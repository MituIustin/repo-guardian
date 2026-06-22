# Repo Guardian — Codex Project Instructions

## Project Context

Repo Guardian is a dissertation project. It is an AI-assisted DevOps platform for monitoring GitHub Actions builds, detecting CI/CD failures, analyzing logs and commits, classifying errors, and generating safe Pull Request proposals through a GitHub App bot.

The existing project already contains a frontend/UI prototype, but it is heavily mocked. It is acceptable to change, redesign, refactor, remove, or rewrite any part of the existing UI if that leads to a cleaner, more maintainable, more production-ready application.

All project code, comments, documentation, commit messages, UI text, API responses, database field names, and Markdown files must be written in English.

## Main Product Goal

The final system should support this end-to-end flow:

1. A user logs in with GitHub.
2. The user connects one or more repositories.
3. Repo Guardian receives GitHub webhook events for workflow/build activity.
4. Failed builds are saved as incidents.
5. GitHub Actions logs are downloaded.
6. Relevant log sections are extracted.
7. AI analyzes logs and explains the likely failure cause.
8. AI analyzes commits/diffs and identifies the likely root cause.
9. The system classifies the error type.
10. The system can generate a safe Pull Request proposal.
11. A GitHub App bot can create a branch, commit changes, and open a Pull Request after user approval.
12. The system records cost, latency, model output quality, and observability metrics.
13. The system provides tests, documentation, deployment files, and evaluation material suitable for a dissertation defense.

## Dissertation Constraints

This project must not be treated as a simple demo. It must be implemented so that it can be explained in a dissertation defense.

Every important decision should be documented in `/docs`.

The implementation should demonstrate:

- clean architecture;
- modular design;
- real GitHub integration;
- LLM abstraction;
- testability;
- observability;
- security-aware design;
- Kubernetes deployment;
- model comparison;
- cost tracking;
- a credible evaluation plan.

## Language and Style Rules

- Use English everywhere.
- Do not use emojis anywhere in code, comments, UI copy, logs, documentation, branch names, commit messages, or test fixtures.
- Keep names clear, explicit, and professional.
- Avoid marketing language.
- Avoid vague labels such as "magic", "AI stuff", "smart thing", or "fix everything".
- Use precise names: `Incident`, `WorkflowRun`, `AIAnalysis`, `PullRequestProposal`, `LLMProvider`, `WebhookEvent`.

## Coding Rules

- Write clean, readable, maintainable code.
- Prefer simple solutions over over-engineered ones.
- Avoid unnecessary abstractions before they are needed.
- Avoid unnecessary dependencies.
- Do not hardcode secrets, tokens, API keys, client secrets, webhook secrets, database passwords, or provider credentials.
- Use environment variables and configuration files.
- Validate all external inputs.
- Verify GitHub webhook signatures.
- Add proper error handling around GitHub API calls, LLM calls, database operations, and queue processing.
- Do not rewrite unrelated files.
- Do not introduce large architectural changes without first explaining the plan.
- Keep tasks small and focused.
- Update tests when changing business logic.
- Update documentation when adding a major feature.

## Existing Frontend Instructions

The current frontend is a mocked prototype and can be heavily changed.

The redesign should aim for a polished, credible, production-grade developer tool. The UI should not look like a student mockup.

Important frontend goals:

- improve dashboard structure;
- improve repository list;
- improve build/incidents overview;
- improve failed build investigation page;
- improve AI diagnosis display;
- improve Pull Request proposal flow;
- improve filters, search, empty states, loading states, and error states;
- avoid cluttered layouts;
- avoid inconsistent status labels;
- avoid unclear technical labels;
- use consistent terminology across the whole product.

The frontend should support the future real backend and should gradually remove mock data.

## UI/UX Principles

Use the following principles when redesigning the interface:

- high contrast and visual accessibility;
- clear visual hierarchy;
- consistent terminology;
- logical filtering and organization;
- progressive disclosure;
- clear build status indicators;
- large readable code diffs and log sections;
- safe action confirmation for risky actions;
- clear distinction between AI diagnosis, evidence, recommended fix, and Pull Request proposal;
- no decorative complexity that reduces usability.

## Architecture Direction

Start with a modular monolith. Do not start with full microservices before the core workflow works.

The initial implementation should have clear internal modules that can later be extracted into services:

- Auth Module
- Repository Management Module
- GitHub Integration Module
- Webhook Processing Module
- CI Monitoring Module
- Incident Management Module
- Log Processing Module
- AI Analysis Module
- LLM Provider Module
- Pull Request Automation Module
- Notification Module
- Observability Module

Later, selected modules can be extracted into independent services:

- API Service
- Webhook Service
- Analysis Worker
- LLM Gateway
- PR Automation Service
- Notification Service

## Feature Implementation Order

Build the project in this order:

1. Clean repository structure and documentation.
2. Improved frontend foundation.
3. Backend API foundation.
4. Database schema.
5. GitHub OAuth login.
6. Repository connection.
7. GitHub webhook endpoint.
8. Workflow run persistence.
9. Incident creation for failed builds.
10. GitHub Actions logs download.
11. Log parsing and relevant section extraction.
12. AI log analysis.
13. AI commit/diff analysis.
14. Error classification.
15. Pull Request proposal generation.
16. GitHub App bot PR creation.
17. LLM abstraction layer.
18. Multiple LLM providers.
19. Cost tracking.
20. Unit and integration tests.
21. E2E tests.
22. Notifications.
23. Observability with Prometheus and Grafana.
24. Docker Compose refinement.
25. Kubernetes deployment.
26. Model comparison and dissertation evaluation.

Do not implement Kubernetes, microservices, multi-provider LLM comparison, or advanced AI flows before the core build-to-incident-to-analysis workflow is functional.

## LLM Integration Rules

All LLM access must go through an abstraction layer.

Business modules must not call provider SDKs directly.

Expected provider abstractions:

- `OpenAIProvider`
- `AnthropicProvider`
- `GeminiProvider`
- `LocalProvider` or `OllamaProvider`
- `MockProvider`

The mock provider must be used in tests.

For every LLM call, record:

- provider;
- model;
- prompt version;
- input tokens;
- output tokens;
- latency;
- estimated cost;
- success or failure;
- error message, if any;
- structured output;
- related incident;
- related repository;
- related workflow run.

LLM responses should be structured, preferably JSON. The system must validate and parse responses safely.

## GitHub Integration Rules

Use GitHub OAuth for user login.

Use a GitHub App for repository-level automation, webhook registration, and Pull Request creation.

Webhook payloads must be verified with the GitHub signature.

Do not merge Pull Requests automatically.

Do not push directly to the default branch.

The AI may suggest a fix, but the user must approve PR creation.

PRs generated by Repo Guardian must clearly state:

- the probable root cause;
- evidence from logs;
- files changed;
- risk level;
- verification steps;
- whether the fix was AI-generated;
- limitations or uncertainty.

## Testing Expectations

Add tests for all meaningful logic.

Expected test categories:

- Unit tests for parsers, classifiers, prompt builders, cost calculators, signature validators, mappers, and response parsers.
- Integration tests for API + database flows.
- Integration tests for webhook payloads and incident creation.
- E2E tests for user flows.
- Mock GitHub clients.
- Mock LLM providers.
- Fixture-based tests using sample GitHub webhook payloads and build logs.

Do not rely on real GitHub or real LLM calls in automated tests.

## Documentation Expectations

Update `/docs` whenever a major feature is introduced.

Maintain these files:

- `docs/vision.md`
- `docs/requirements.md`
- `docs/roadmap.md`
- `docs/architecture.md`
- `docs/data-model.md`
- `docs/api-contract.md`
- `docs/ui-redesign.md`
- `docs/github-integration.md`
- `docs/ai-llm-strategy.md`
- `docs/testing-strategy.md`
- `docs/kubernetes-plan.md`
- `docs/observability-plan.md`
- `docs/security.md`
- `docs/evaluation-plan.md`
- `docs/dissertation-notes.md`

## Before Editing

Before making non-trivial changes, explain briefly:

1. what you will change;
2. why the change is needed;
3. which files will be touched;
4. how the change will be tested.

After making changes, summarize:

1. what changed;
2. which tests were added or updated;
3. how to run the project;
4. what the next logical task is.

## Forbidden Behavior

Do not:

- add emojis;
- hardcode secrets;
- skip webhook signature validation;
- create AI-generated PRs without user approval;
- auto-merge Pull Requests;
- call LLM providers directly from unrelated modules;
- hide errors silently;
- introduce large undocumented rewrites;
- create microservices before the modular monolith is stable;
- add Kubernetes before the application has a working end-to-end flow;
- leave mock data mixed with real production flows without clear separation;
- use vague or inconsistent terminology in the UI.
