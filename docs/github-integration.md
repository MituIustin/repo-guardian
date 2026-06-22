# GitHub Integration Plan

## Goal

Repo Guardian must integrate deeply with GitHub in a safe and controlled way.

The integration has four major parts:

1. GitHub OAuth login.
2. Repository connection.
3. GitHub webhooks for workflow activity.
4. GitHub App installation for repository access and future Pull Request automation.

## Implementation Status

GitHub OAuth, repository connection, GitHub App installation, and workflow monitoring are implemented. OAuth includes state validation, profile and verified primary-email retrieval, encrypted access-token persistence, signed sessions, repository discovery, branch validation, connection persistence, logout, and automated tests with mocked GitHub requests.

OAuth requests the `repo` scope so authenticated users can select accessible public and private repositories. Existing sessions issued before this scope was introduced must be authorized again.

## Implemented Workflow Monitoring

The GitHub App replaces manual per-repository webhook configuration. A user starts installation from the repository page, GitHub redirects to the authenticated setup callback, and Repo Guardian synchronizes every repository selected for that installation. Existing connections are matched by GitHub repository ID and retain their monitored branch. New connections initially monitor the repository's default branch.

Repo Guardian verifies `X-Hub-Signature-256`, deduplicates `X-GitHub-Delivery`, persists matching monitored-branch runs, retrieves jobs, and downloads logs for failed completed runs. Workflow processing prefers a short-lived GitHub App installation token. The encrypted OAuth token remains a compatibility fallback for manually connected repositories.

Pull Request creation and its Contents and Pull requests permissions remain deferred until the human-approved remediation milestone.

## GitHub App Installation

The installation flow uses these endpoints:

```text
GET /api/github-app/status
GET /api/github-app/install
GET /api/github-app/setup
DELETE /api/github-app/installations/{installation_id}
```

The install endpoint records a state value in the signed session. The setup callback validates that state before accepting the GitHub installation ID. The backend signs an RS256 app JWT from the base64-encoded private key, exchanges it for a short-lived installation token, and lists the installation repositories.

Installation and repository-selection webhook events keep known installations synchronized. An installation is associated with the authenticated Repo Guardian user during setup. Installations may cover a personal account or organization, so one user can have multiple installation records.

The OAuth identity remains the Repo Guardian login identity. GitHub App installations are separate access sources and may belong to other personal accounts or organizations that the authenticated user is authorized to install the App for. Repository reads and rerun actions prefer that repository's installation token rather than assuming the OAuth identity owns the repository.

Users can synchronize or disconnect each installation independently. Individual repository disconnections are retained as exclusions during automatic webhook synchronization. A deliberate installation reconnection restores all repositories selected in GitHub.

Disconnecting repositories is reversible and only pauses Repo Guardian monitoring. Disconnecting an account calls GitHub's installation deletion endpoint with App authentication, marks the local installation deleted, and deactivates its repository connections. The UI requires explicit confirmation before this external action.

Current minimum repository permissions:

```text
Actions: Read and write
Metadata: Read-only
```

Current event subscription:

```text
Workflow run
```

## GitHub OAuth

Use OAuth for user authentication.

Purpose:

- identify the user;
- retrieve basic profile information;
- list repositories available to the user;
- associate GitHub identity with Repo Guardian account.

Important data:

```text
github_user_id
username
display_name
avatar_url
access_token
```

Security:

- tokens must not be stored in plain text;
- use environment variables for OAuth client credentials;
- handle token expiration or revocation.

Current implementation details:

- OAuth state is stored in a signed, HTTP-only session and compared before code exchange;
- access tokens are encrypted with an environment-provided Fernet key;
- sessions contain only the internal user identifier;
- provider errors are returned without exposing tokens or GitHub response bodies;
- automated tests use mocked HTTP transport and never call GitHub.

## Repository Connection

Users should be able to connect repositories that they have permission to access.

Repository metadata:

```text
github_repository_id
owner
name
full_name
default_branch
visibility
html_url
clone_url
```

Connection metadata:

```text
user_id
repository_id
github_account_id
installation_id
monitored_branch
is_active
```

## GitHub Webhooks

Use GitHub webhooks to detect workflow activity.

Initial event:

```text
workflow_run
```

Future events:

```text
check_run
check_suite
push
pull_request
```

Webhook endpoint:

```text
POST /api/webhooks/github
```

Required headers:

```text
X-GitHub-Event
X-GitHub-Delivery
X-Hub-Signature-256
```

Processing rules:

1. Verify signature.
2. Check delivery ID for duplicates.
3. Store webhook metadata.
4. Process supported event type.
5. Ignore unsupported event types safely.
6. Return quickly.
7. Queue long-running processing.

After an installation, repository-selection, or workflow webhook changes repository state, the API emits `repositories.changed` over the authenticated repository WebSocket. The frontend then reloads authoritative repository and installation counts.

## Workflow Reruns

The Builds workspace provides explicit, confirmed actions for:

```text
rerun complete workflow
rerun failed jobs
rerun individual job
```

The backend verifies that the user has an active connection to the build repository, requests a short-lived installation token, and sends the rerun request to GitHub. GitHub webhook events remain the source of truth for the resulting run state.

GitHub job responses include structured step names, order, status, conclusion, and timestamps. Repo Guardian stores this bounded metadata with the job so users can inspect the execution sequence without loading raw logs.

## Workflow Run Processing

For `workflow_run` payloads, extract:

```text
repository
workflow_run.id
workflow_run.name
workflow_run.status
workflow_run.conclusion
workflow_run.head_branch
workflow_run.head_sha
workflow_run.html_url
workflow_run.run_number
workflow_run.run_attempt
workflow_run.created_at
workflow_run.updated_at
```

If conclusion is `failure`, create an incident.

## GitHub Actions Logs

For failed workflow runs:

1. request log download;
2. store raw log or file reference;
3. parse relevant sections;
4. attach sections to incident;
5. queue AI analysis.

Log processing should run in a worker.

## Commit and Diff Analysis

For a failed workflow run, retrieve:

- head commit;
- commit message;
- author;
- changed files;
- diff;
- parent commit if needed.

The AI module should receive only relevant context, not the entire repository.

## GitHub App Bot

Use the existing GitHub App for repository automation. Installation, repository synchronization, webhook delivery, and Actions read access are implemented; write operations remain deferred.

The GitHub App should be used for:

- webhook registration;
- repository permissions;
- branch creation;
- committing AI-suggested changes;
- opening Pull Requests.

Future Pull Request automation may require:

```text
contents
pull_requests
actions
checks
metadata
```

Exact permissions should be minimized and documented.

## Pull Request Creation Flow

1. User opens incident.
2. User reviews AI diagnosis.
3. User generates PR proposal.
4. System shows diff.
5. User approves proposal.
6. GitHub App creates branch.
7. GitHub App commits changes.
8. GitHub App opens Pull Request.
9. Repo Guardian stores PR metadata.

## Safety Rules

- Never push to default branch.
- Never merge automatically.
- Never create PR without user approval.
- Include AI-generated disclosure in PR description.
- Include evidence and uncertainty.
- Include verification steps.
- Avoid modifying unrelated files.
- Prefer minimal changes.

## PR Description Template

```text
## Summary

This Pull Request was generated by Repo Guardian to address a failed CI/CD workflow.

## Probable Cause

[AI diagnosis summary]

## Evidence

- [Log evidence line or section]
- [Commit/diff evidence]

## Changes

- [File changed]
- [Reason]

## Risk Level

[Low / Medium / High / Critical]

## Verification Steps

1. Run the affected workflow.
2. Run the relevant test suite.
3. Review the changed files manually.

## Notes

This Pull Request was generated with AI assistance and requires human review before merging.
```

## Error Handling

Handle:

- invalid webhook signatures;
- duplicate webhook deliveries;
- missing repository mapping;
- GitHub API rate limits;
- log download failures;
- missing permissions;
- token expiration;
- PR creation conflicts;
- branch already exists.

## Testing

Use fixtures for:

- `workflow_run` success;
- `workflow_run` failure;
- duplicate delivery;
- invalid signature;
- missing repository;
- failed log download.

Do not depend on real GitHub calls in automated tests.
