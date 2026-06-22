# API Contract

## API Style

The initial API can be REST-based.

Implementation status: health, readiness, GitHub authentication, GitHub App installation, repository synchronization, signed workflow webhooks, build reads, and build WebSocket updates are available.

Recommended base path:

```text
/api
```

All responses should be JSON.

Use clear English field names.

## Common Response Patterns

### Success

```json
{
  "data": {}
}
```

### List Response

```json
{
  "data": [],
  "pagination": {
    "page": 1,
    "pageSize": 20,
    "total": 100
  }
}
```

### Error Response

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request is invalid.",
    "details": []
  }
}
```

## Health

### GET `/api/health`

Returns service health.

Response:

```json
{
  "status": "ok",
  "service": "repo-guardian-api",
  "version": "0.1.0"
}
```

### GET `/api/ready`

Checks whether the API can accept application traffic and query PostgreSQL.

Ready response:

```json
{
  "status": "ready",
  "service": "repo-guardian-api",
  "version": "0.1.0",
  "checks": {
    "database": "ok"
  }
}
```

When PostgreSQL is unavailable, the endpoint returns HTTP `503` with `status` set to `not_ready` and `checks.database` set to `unavailable`. Connection details and database errors are not exposed.

## Auth

### GET `/api/auth/github/login`

Starts GitHub OAuth login.

The endpoint creates a signed-session OAuth state value and redirects to GitHub. It returns HTTP `503` when GitHub OAuth environment variables are absent.

### GET `/api/auth/github/callback`

Handles GitHub OAuth callback.

The callback validates OAuth state, exchanges the authorization code, loads the GitHub profile, encrypts the access token, persists the user and GitHub account, and redirects to the frontend. Invalid or expired state returns HTTP `400`.

### GET `/api/auth/me`

Returns the current user.

Response:

```json
{
  "data": {
    "id": "user-id",
    "name": "User Name",
    "email": "user@example.com",
    "avatarUrl": "https://example.com/avatar.png"
  }
}
```

### POST `/api/auth/logout`

Logs out the current user.

Response:

```json
{
  "status": "ok"
}
```

## GitHub App

### GET `/api/github-app/status`

Returns whether the GitHub App is configured, the total synchronized repository count, and every non-deleted installation linked to the authenticated user.

### GET `/api/github-app/install`

Creates a session-bound installation state and redirects the authenticated user to GitHub. It returns HTTP `503` when the App ID, slug, or private key is unavailable.

### GET `/api/github-app/setup`

Validates the session state and GitHub installation ID, synchronizes the installation repositories, and redirects to the repository page. Existing monitored branches are preserved.

### POST `/api/github-app/installations/{installationId}/synchronize`

Refreshes one installation. It reconnects the selected repositories when monitoring was previously disabled.

### DELETE `/api/github-app/installations/{installationId}/repositories`

Disconnects all active repositories from one installation without uninstalling the GitHub App.

### DELETE `/api/github-app/installations/{installationId}`

Uninstalls the GitHub App from the linked account or organization and deactivates its repository connections. This is a confirmed external action.

## Repositories

### GET `/api/repositories`

Lists connected repositories.

Response:

```json
{
  "data": [
    {
      "id": "repository-id",
      "name": "repo",
      "fullName": "owner/repo",
      "visibility": "private",
      "htmlUrl": "https://github.com/owner/repo",
      "defaultBranch": "main",
      "monitoredBranch": "main",
      "isActive": true,
      "webhookStatus": "configured",
      "connectedAt": "2026-06-21T12:00:00Z"
    }
  ]
}
```

### GET `/api/repositories/available`

Lists GitHub repositories available for connection. The optional `installation_id` query parameter scopes the result to one linked GitHub App source; without it, the OAuth login identity is used.

### GET `/api/repositories/available/{githubRepositoryId}/branches`

Lists branches for an accessible GitHub repository. The optional `installation_id` query parameter selects the GitHub App credential used for repositories from another account or organization.

### POST `/api/repositories/connect`

Connects a repository.

Request:

```json
{
  "githubRepositoryId": 123456,
  "monitoredBranch": "main",
  "installationId": 77
}
```

### GET `/api/repositories/{repositoryId}`

Returns repository details.

### PATCH `/api/repositories/{repositoryId}`

Updates repository settings.

Request:

```json
{
  "monitoredBranch": "develop"
}
```

### DELETE `/api/repositories/{repositoryId}`

Disconnects a repository.

### DELETE `/api/repositories`

Disconnects all active repositories and disables automatic monitoring for the user's GitHub App installations. Installation records remain available for explicit reconnection.

### WebSocket `/api/repositories/stream`

Requires the authenticated session cookie. It emits `repositories.changed` after connection mutations and relevant GitHub webhook processing. Clients reload authoritative REST resources when notified.

## Webhooks

### POST `/api/webhooks/github`

Receives GitHub webhook events.

Headers:

```text
X-GitHub-Event
X-GitHub-Delivery
X-Hub-Signature-256
```

Valid `workflow_run`, `installation`, and `installation_repositories` deliveries return HTTP `202`. Signatures are verified before parsing, delivery IDs are deduplicated, and unsupported events are recorded as ignored.

Requirements:

- verify signature;
- deduplicate delivery ID;
- process `workflow_run`;
- create incident when workflow failed.

Response:

```json
{
  "status": "accepted"
}
```

### WebSocket `/api/builds/stream`

Requires the authenticated session cookie. It emits `builds.connected` followed by committed `workflow_run.updated` messages containing the same build shape returned by the REST API.

## Builds

### GET `/api/builds`

Returns the authenticated user's workflow runs for active repository connections, including jobs, structured steps, GitHub links, and the latest stored error excerpt.

### POST `/api/builds/{buildId}/rerun`

Requests a GitHub workflow rerun. The JSON body contains `mode` with `all` or `failed`. Only completed runs belonging to an active user repository connection are accepted.

### POST `/api/builds/jobs/{jobId}/rerun`

Requests a rerun of one completed GitHub Actions job belonging to an active user repository connection.

## Workflow Runs

### GET `/api/repositories/{repositoryId}/workflow-runs`

Lists workflow runs for a repository.

Query parameters:

```text
status
conclusion
branch
page
pageSize
```

### GET `/api/workflow-runs/{workflowRunId}`

Returns workflow run details.

Response:

```json
{
  "data": {
    "id": "workflow-run-id",
    "workflowName": "CI",
    "status": "completed",
    "conclusion": "failure",
    "branch": "main",
    "commitSha": "abc123",
    "startedAt": "2026-01-01T10:00:00Z",
    "completedAt": "2026-01-01T10:04:00Z",
    "jobs": []
  }
}
```

## Incidents

### GET `/api/incidents`

Lists incidents.

Query parameters:

```text
repositoryId
status
severity
category
page
pageSize
```

### GET `/api/incidents/{incidentId}`

Returns incident details.

Response:

```json
{
  "data": {
    "id": "incident-id",
    "title": "CI failed on main",
    "status": "open",
    "severity": "medium",
    "category": "dependency_error",
    "confidence": 0.87,
    "summary": "The workflow failed during dependency installation.",
    "workflowRun": {},
    "latestAnalysis": {},
    "timeline": []
  }
}
```

### PATCH `/api/incidents/{incidentId}`

Updates incident status or metadata.

Request:

```json
{
  "status": "resolved"
}
```

## Logs

### POST `/api/incidents/{incidentId}/logs/fetch`

Queues log download.

Response:

```json
{
  "status": "queued"
}
```

### GET `/api/incidents/{incidentId}/logs`

Returns stored log sections.

Response:

```json
{
  "data": [
    {
      "id": "log-section-id",
      "jobName": "build",
      "stepName": "Install dependencies",
      "startLine": 120,
      "endLine": 165,
      "sectionType": "error",
      "content": "..."
    }
  ]
}
```

## AI Analysis

### POST `/api/incidents/{incidentId}/ai/analyze-logs`

Queues AI log analysis.

Request:

```json
{
  "provider": "openai",
  "model": "selected-model"
}
```

Response:

```json
{
  "status": "queued"
}
```

### POST `/api/incidents/{incidentId}/ai/analyze-commit`

Queues AI commit analysis.

### GET `/api/incidents/{incidentId}/ai/analyses`

Lists AI analyses for an incident.

### GET `/api/ai/models`

Lists configured LLM providers and models.

Response:

```json
{
  "data": [
    {
      "provider": "openai",
      "models": ["model-name"]
    }
  ]
}
```

## Pull Request Proposals

### POST `/api/incidents/{incidentId}/pr-proposals`

Generates a Pull Request proposal.

Response:

```json
{
  "status": "queued"
}
```

### GET `/api/incidents/{incidentId}/pr-proposals`

Lists proposals.

### GET `/api/pr-proposals/{proposalId}`

Returns proposal details.

### POST `/api/pr-proposals/{proposalId}/approve`

Approves a proposal.

### POST `/api/pr-proposals/{proposalId}/create-pr`

Creates a GitHub Pull Request after approval.

Response:

```json
{
  "data": {
    "pullRequestUrl": "https://github.com/owner/repo/pull/1"
  }
}
```

## Notifications

### GET `/api/notifications`

Lists user notifications.

### POST `/api/notifications/{notificationId}/read`

Marks a notification as read.

## Metrics

### GET `/metrics`

Prometheus metrics endpoint.

## API Design Rules

- Use English names.
- Keep response fields consistent.
- Avoid leaking internal IDs where not needed.
- Avoid leaking secrets or raw tokens.
- Return clear error messages.
- Do not expose raw full logs by default if they may contain secrets.
- Add pagination for large lists.
