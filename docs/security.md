# Security Plan

## Goal

Repo Guardian integrates with GitHub repositories, build logs, LLM providers, and Pull Request automation. Security must be considered from the beginning.

## Main Security Risks

### GitHub Token Exposure

Risk:

OAuth tokens or GitHub App credentials could be exposed.

Mitigation:

- do not hardcode tokens;
- use environment variables;
- encrypt tokens at rest if stored;
- avoid logging tokens;
- rotate credentials if compromised.

### Webhook Spoofing

Risk:

An attacker could send fake webhook events.

Mitigation:

- verify `X-Hub-Signature-256`;
- reject invalid signatures;
- store delivery IDs;
- deduplicate events.

### Unauthorized Repository Access

Risk:

Users could access repositories they do not own or are not authorized to view.

Mitigation:

- enforce repository ownership/connection checks;
- associate repositories with users and GitHub accounts;
- check authorization in every repository and incident endpoint.

### Sensitive Data in Logs

Risk:

Build logs may contain secrets.

Mitigation:

- redact known secret patterns;
- avoid sending unnecessary log content to LLMs;
- avoid showing full logs by default;
- restrict log access to authorized users;
- document that logs may contain sensitive data.

### Unsafe AI-Generated Changes

Risk:

AI may generate incorrect, insecure, or destructive changes.

Mitigation:

- require user approval before PR creation;
- never auto-merge Pull Requests;
- never push to default branch;
- show diffs before PR creation;
- include risk level and verification steps;
- keep changes minimal.

### LLM Data Exposure

Risk:

Sending logs and code diffs to external LLM providers may expose sensitive data.

Mitigation:

- send only relevant excerpts;
- redact secrets;
- allow provider configuration;
- support local provider later;
- document data sent to providers;
- add user or admin controls where possible.

### GitHub App Over-Permission

Risk:

The GitHub App may request more permissions than needed.

Mitigation:

- request minimum permissions;
- document each permission;
- separate read-only from write actions;
- require explicit approval before write actions.

## Authentication Rules

- Use GitHub OAuth for login.
- Protect all authenticated endpoints.
- Use secure session or token handling.
- Implement logout.
- Avoid exposing authentication details in client logs.

Implemented controls:

- signed, HTTP-only session cookie with `SameSite=Lax`;
- cryptographically random OAuth state and constant-time comparison;
- encrypted GitHub access tokens using an environment-provided Fernet key;
- no access tokens in browser storage or API responses;
- configurable secure-cookie mode for HTTPS deployments;
- generic provider failure messages that do not expose credentials.

## Authorization Rules

Every endpoint involving repositories, incidents, logs, analyses, or Pull Requests must verify that the current user has access.

Important checks:

```text
user can access repository
repository is connected
incident belongs to repository
analysis belongs to incident
PR proposal belongs to incident
```

## Webhook Security

Required:

- verify signature;
- reject invalid signatures;
- deduplicate delivery ID;
- process only supported events;
- avoid trusting payload blindly.

Implemented controls include HMAC-SHA256 verification before JSON parsing, delivery-ID uniqueness, Pydantic payload validation, monitored-repository and branch checks, session-bound GitHub App setup state, an environment-provided RSA private key, short-lived installation tokens that are not persisted, archive size limits, bounded excerpts, and common credential redaction. Raw webhook payloads and full log archives are not persisted.

Workflow and job reruns require an authenticated user, an active repository connection, a completed stored run or job, and explicit confirmation in the UI. The GitHub App has Actions write access only because reruns are an implemented user-requested operation; Repo Guardian does not modify workflow files through this permission.

Account disconnection verifies installation ownership, requires UI confirmation, and uses an App JWT to delete only the selected GitHub installation. Local connections are deactivated only after GitHub accepts the uninstall request.

## Secrets Management

Required environment variables:

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

Rules:

- never commit real `.env` files;
- commit only `.env.example`;
- never commit Kubernetes real secrets;
- commit only `secrets.example.yaml`.

## Pull Request Safety

Rules:

- user approval required;
- no auto-merge;
- no direct push to default branch;
- PR branch names must be predictable and safe;
- generated PR must include disclosure;
- generated PR must include verification steps;
- high-risk changes must be clearly marked.

## Logging Rules

Do not log:

- access tokens;
- API keys;
- private keys;
- webhook secrets;
- full raw logs unless redacted;
- sensitive headers.

Use structured logs without secrets.

## Dissertation Security Discussion

The dissertation should include a section explaining:

- webhook verification;
- human-in-the-loop PR generation;
- token handling;
- LLM data exposure risks;
- secret redaction;
- authorization checks;
- limitations.
