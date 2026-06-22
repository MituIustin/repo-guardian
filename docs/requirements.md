# Requirements

## Functional Requirements

### Authentication

The system must allow users to authenticate with GitHub.

Requirements:

- GitHub OAuth login.
- User profile persistence.
- GitHub account association.
- Session or token-based authentication.
- Current user endpoint.
- Logout flow.

### Repository Management

The system must allow users to connect and manage GitHub repositories.

Requirements:

- List accessible repositories.
- Connect a repository to Repo Guardian.
- Store repository metadata.
- Show repository status.
- Show monitored branch.
- Show recent workflow activity.
- Allow disconnecting a repository.

### GitHub Webhooks

The system must receive GitHub webhook events.

Requirements:

- Endpoint for GitHub webhook payloads.
- Signature verification.
- Support for `workflow_run` events.
- Future support for `check_run`, `check_suite`, `push`, and `pull_request`.
- Store raw webhook payload metadata for debugging.
- Avoid duplicate processing using GitHub delivery IDs.

### Build and Incident Persistence

The system must persist CI/CD workflow data.

Requirements:

- Store workflow runs.
- Store build jobs.
- Store failed steps when available.
- Create incidents for failed workflow runs.
- Track incident status.
- Track incident severity.
- Track incident category.
- Track incident timeline events.

### GitHub Actions Logs

The system must download logs for failed workflow runs.

Requirements:

- Download workflow run logs.
- Store raw logs or references to stored logs.
- Extract relevant log sections.
- Identify failed job, step, and command where possible.
- Support large logs without blocking the main API request.
- Use background processing for log download and parsing.

### AI Log Analysis

The system must analyze failed build logs using LLMs.

Requirements:

- Use an LLM abstraction layer.
- Generate structured diagnosis.
- Classify error category.
- Provide confidence score.
- Extract evidence lines.
- Provide recommended action.
- Store the full analysis result.
- Track provider, model, latency, token usage, and cost.

### AI Commit Analysis

The system must analyze commits and diffs related to failed builds.

Requirements:

- Identify suspicious commit candidates.
- Retrieve commit metadata.
- Retrieve relevant diffs.
- Compare changed files with log error context.
- Explain likely root cause.
- Identify affected files.
- Provide risk level.
- Recommend next action.

### Pull Request Proposal

The system must generate Pull Request proposals.

Requirements:

- Generate a proposed fix.
- Show diff before creating a PR.
- Require user approval.
- Create a new branch through the GitHub App bot.
- Commit changes.
- Open a Pull Request.
- Include diagnosis, evidence, and verification steps in the PR description.
- Never merge automatically.

### LLM Provider Abstraction

The system must support multiple LLM providers through a common interface.

Requirements:

- Provider interface.
- OpenAI provider.
- Mock provider.
- Future Anthropic provider.
- Future Gemini provider.
- Future local provider.
- Model configuration.
- Prompt versioning.
- Cost calculation.
- Response validation.

### Model Comparison

The system should compare LLM providers and models.

Requirements:

- Store outputs per model.
- Compare classification accuracy.
- Compare latency.
- Compare cost.
- Compare JSON validity rate.
- Compare evidence quality.
- Compare usefulness of suggested fixes.
- Support an evaluation dataset.

### Notifications

The system should notify users about important events.

Requirements:

- In-app notifications.
- Email notifications.
- Future Slack or Discord notifications.
- Notification preferences.
- Events for build failed, analysis completed, PR proposal ready, and PR created.

### Observability

The system must expose metrics and logs.

Requirements:

- Application metrics.
- Queue metrics.
- LLM request metrics.
- GitHub API error metrics.
- Incident metrics.
- Prometheus scraping support.
- Grafana dashboards.

### Deployment

The system must support local and containerized deployment.

Requirements:

- Docker Compose for local development.
- Kubernetes manifests for advanced deployment.
- Environment-based configuration.
- Health checks.
- Readiness and liveness probes.
- Worker scalability.

## Non-Functional Requirements

### Maintainability

- Code must be clean and readable.
- Modules must have clear boundaries.
- Large files should be avoided.
- Shared logic should be extracted only when needed.
- Documentation must stay updated.

### Security

- No hardcoded secrets.
- GitHub webhook signatures must be verified.
- Tokens must be stored securely.
- Pull Request creation must require explicit user approval.
- API endpoints must enforce authorization.
- Logs must avoid exposing secrets.

### Performance

- Webhook endpoints should respond quickly.
- Heavy tasks should run in background workers.
- Large logs should be processed efficiently.
- LLM calls should be asynchronous where possible.
- Dashboard pages should not block on long-running analysis.

### Reliability

- Background jobs should be retryable.
- Duplicate webhook deliveries should not create duplicate incidents.
- GitHub API rate limits should be handled.
- LLM provider failures should be handled gracefully.
- The system should show useful error states.

### Testability

- Business logic must be testable without real GitHub or real LLM providers.
- External integrations must have mocks.
- Tests must cover webhook validation, log parsing, AI response parsing, cost tracking, and PR proposal creation.

### Academic Quality

- Architectural decisions must be documented.
- The evaluation methodology must be explicit.
- The project must include measurable results.
- Limitations must be acknowledged.
