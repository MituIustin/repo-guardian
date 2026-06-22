# Testing Strategy

## Goal

Repo Guardian must have a serious testing strategy because it integrates external systems, background processing, LLM calls, and GitHub automation.

Tests should make the system reliable and easier to explain in a dissertation defense.

## Test Types

### Unit Tests

Use unit tests for isolated logic.

Target areas:

- webhook signature validation;
- GitHub payload mapping;
- incident creation rules;
- log parsing;
- log section extraction;
- error classification;
- prompt building;
- LLM response parsing;
- cost calculation;
- Pull Request proposal state transitions;
- notification rules.

### Integration Tests

Use integration tests for multiple components working together.

Target flows:

- webhook payload to workflow run persistence;
- failed workflow to incident creation;
- incident to log download request;
- log sections to AI analysis request;
- AI analysis to stored result;
- PR proposal to PR creation request.

Use test database containers if possible.

### E2E Tests

Use E2E tests for main user flows.

Recommended tool:

- Playwright or Cypress.

Target flows:

1. User logs in.
2. User connects repository.
3. Failed workflow appears as incident.
4. User opens incident details.
5. User views log evidence.
6. User runs AI analysis.
7. User reviews PR proposal.
8. User creates Pull Request.

### Contract Tests

Use contract tests if microservices are extracted.

Target contracts:

- API to worker;
- API to LLM Gateway;
- API to Notification Service;
- Webhook Service to CI Monitoring Service.

## Test Fixtures

Create fixtures for:

```text
GitHub workflow_run success payload
GitHub workflow_run failure payload
GitHub invalid signature payload
GitHub duplicate delivery
GitHub Actions dependency failure log
GitHub Actions test failure log
GitHub Actions Docker failure log
GitHub Actions missing secret log
GitHub Actions lint failure log
LLM valid JSON response
LLM invalid JSON response
LLM provider timeout
```

Recommended folder:

```text
tests/fixtures/
  github-webhooks/
  build-logs/
  llm-responses/
  diffs/
```

## Mocking Rules

Do not call real GitHub APIs in automated tests.

Do not call real LLM APIs in automated tests.

Required mocks:

```text
MockGitHubClient
MockLLMProvider
MockNotificationProvider
MockQueue
```

## Unit Test Examples

### Webhook Signature Validator

Cases:

- valid signature;
- invalid signature;
- missing signature;
- modified payload;
- wrong secret.

### Log Parser

Cases:

- extracts failed command;
- extracts stack trace;
- handles large logs;
- handles empty logs;
- handles logs without clear error.

### LLM Response Parser

Cases:

- valid JSON;
- missing required fields;
- invalid category;
- confidence out of range;
- malformed JSON;
- empty response.

### Cost Calculator

Cases:

- calculates input cost;
- calculates output cost;
- handles unknown model;
- handles zero tokens.

## Integration Test Examples

### Failed Workflow Creates Incident

Input:

- fixture `workflow_run_failure.json`

Expected:

- workflow run stored;
- incident created;
- incident status is `open`;
- category is initially `unknown`;
- timeline event created.

### Log Analysis Stores Result

Input:

- incident;
- log section;
- mock LLM response.

Expected:

- AIAnalysis stored;
- category updated;
- confidence updated;
- evidence stored;
- timeline event created.

## E2E Test Examples

### Incident Investigation Flow

Steps:

1. Login with mocked session.
2. Open dashboard.
3. Open incidents page.
4. Select failed incident.
5. View log evidence.
6. Start AI analysis.
7. Wait for analysis completed state.
8. Review diagnosis.

### Pull Request Proposal Flow

Steps:

1. Open analyzed incident.
2. Click `Generate PR proposal`.
3. Review diff.
4. Approve proposal.
5. Click `Create Pull Request`.
6. Confirm PR URL is shown.

## CI Pipeline

The project should run tests automatically on GitHub Actions.

Pipeline stages:

```text
install
lint
typecheck
unit tests
integration tests
frontend build
backend build
E2E tests
Docker build
```

## Test Naming Rules

Use clear names.

Good:

```text
should_create_incident_when_workflow_run_fails
should_reject_webhook_when_signature_is_invalid
should_parse_dependency_error_from_npm_log
```

Bad:

```text
test1
works
github test
```

## Dissertation Use

Implemented integration tests cover webhook HMAC validation, rejected signatures, GitHub App JWT signing and API mapping, installation and bulk repository route authentication, GitHub workflow and job rerun mapping, GitHub job and log mapping, archive parsing, secret redaction, schema migration, authenticated repository-source rendering, build rerun controls, and production compilation. Automated tests never call GitHub.

GitHub client tests also verify installation deletion authentication and structured job-step mapping. Frontend tests exercise source-first manual selection and progressive build-detail expansion.

Testing can be discussed in the dissertation as proof of:

- reliability;
- maintainability;
- integration correctness;
- safe AI automation;
- controlled external dependencies.
