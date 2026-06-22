# Data Model

## Overview

The data model should support GitHub authentication, repository monitoring, workflow runs, incidents, logs, AI analysis, Pull Request proposals, cost tracking, and notifications.

This model is intentionally designed for the first production-oriented version. It can be simplified during early implementation if needed.

## Implemented Foundation Schema

Migration `0001` implements `User`, `GitHubAccount`, `Repository`, `WorkflowRun`, `BuildJob`, and `Incident`.

All internal identifiers are UUIDs and timestamps are timezone-aware. GitHub identifiers are stored as unique big integers. `Incident.failed_job_id` is nullable because an incident may be created before job details are available; deleting the referenced job sets this field to null.

Migration `0002` adds encrypted OAuth credential storage. Migration `0003` adds `RepositoryConnection` for user-owned monitoring configuration.

Migration `0004` implements `WebhookDelivery` and `BuildLogExcerpt`. It also records webhook status and the last verified delivery time on `RepositoryConnection`. Full raw logs are not persisted; only bounded, redacted failure evidence is stored.

Migration `0005` implements `GitHubAppInstallation`. It records the GitHub account or organization installation and synchronization state. Private keys and installation access tokens are never stored in this table.

Migration `0006` adds `GitHubAppInstallation.monitoring_enabled`. This distinguishes an installed GitHub source from one intentionally disconnected in Repo Guardian.

Migration `0007` adds `BuildJob.steps` as JSONB. It stores bounded structured step metadata returned by GitHub: name, number, status, conclusion, and timestamps. Raw step logs remain outside this field.

## Main Entities

### User

Represents an application user.

Fields:

```text
id
email
name
avatar_url
created_at
updated_at
last_login_at
```

Relationships:

- has many `GitHubAccount`
- has many `RepositoryConnection`
- has many `Notification`

### GitHubAccount

Represents a GitHub identity connected to a user.

Fields:

```text
id
user_id
github_user_id
username
display_name
avatar_url
access_token_encrypted
refresh_token_encrypted
token_expires_at
created_at
updated_at
```

Relationships:

- belongs to `User`

Security note:

Tokens must not be stored in plain text.

Implementation note: migration `0002` adds `access_token_encrypted`, `token_scope`, and `token_type`. The access token is encrypted with Fernet before persistence. Refresh-token fields remain deferred because the current GitHub OAuth flow does not issue one.

### Repository

Represents a GitHub repository known to Repo Guardian.

Fields:

```text
id
github_repository_id
owner
name
full_name
default_branch
visibility
html_url
clone_url
created_at
updated_at
```

Relationships:

- has many `RepositoryConnection`
- has many `WorkflowRun`
- has many `Incident`

### GitHubAppInstallation

Represents a GitHub App installation connected to a Repo Guardian user.

Fields:

```text
id
user_id
github_installation_id
account_id
account_login
account_type
repository_selection
status
monitoring_enabled
suspended_at
last_synced_at
created_at
updated_at
```

Relationships:

- belongs to `User`
- identifies repository connections through `installation_id`

Security note: installation tokens are requested when needed and remain in memory only.

Connection lifecycle note: `RepositoryConnection.is_active` preserves explicit per-repository exclusions. Automatic GitHub synchronization adds newly selected repositories but does not reactivate an explicitly disconnected connection. Reconnecting a disabled installation restores its selected repositories.

### RepositoryConnection

Represents a user's connection to a repository.

Fields:

```text
id
user_id
repository_id
github_account_id
installation_id
monitored_branch
is_active
created_at
updated_at
```

Relationships:

- belongs to `User`
- belongs to `Repository`
- belongs to `GitHubAccount`

### WebhookDelivery

Stores metadata about GitHub webhook deliveries.

Fields:

```text
id
github_delivery_id
event_type
repository_id
signature_verified
payload_hash
received_at
processed_at
processing_status
error_message
```

Purpose:

- deduplicate GitHub webhook deliveries;
- debug webhook processing;
- track failed processing attempts.

### WorkflowRun

Represents a GitHub Actions workflow run.

Fields:

```text
id
repository_id
github_run_id
workflow_id
workflow_name
run_number
run_attempt
branch
commit_sha
status
conclusion
trigger_event
html_url
started_at
completed_at
created_at
updated_at
```

Relationships:

- belongs to `Repository`
- has many `BuildJob`
- has one or many `Incident`

### BuildJob

Represents a job inside a workflow run.

Fields:

```text
id
workflow_run_id
github_job_id
name
status
conclusion
started_at
completed_at
runner_name
html_url
steps
created_at
updated_at
```

Relationships:

- belongs to `WorkflowRun`

### Incident

Represents a failed build investigation case.

Fields:

```text
id
repository_id
workflow_run_id
failed_job_id
title
status
severity
category
confidence
summary
created_at
updated_at
resolved_at
```

Suggested status values:

```text
open
investigating
analysis_completed
pr_proposed
pr_created
resolved
ignored
```

Suggested severity values:

```text
low
medium
high
critical
```

Suggested category values:

```text
dependency_error
test_failure
syntax_error
lint_error
security_error
configuration_error
permission_error
missing_secret
docker_error
timeout
flaky_test
unknown
```

Relationships:

- belongs to `Repository`
- belongs to `WorkflowRun`
- optionally references the failed `BuildJob`
- has many `BuildLog`
- has many `AIAnalysis`
- has many `PullRequestProposal`
- has many `IncidentTimelineEvent`

### IncidentTimelineEvent

Represents a timeline entry for an incident.

Fields:

```text
id
incident_id
event_type
message
metadata_json
created_at
```

Examples:

```text
workflow_failed
logs_download_started
logs_downloaded
logs_parsed
ai_analysis_started
ai_analysis_completed
pr_proposal_generated
pull_request_created
notification_sent
```

### BuildLog

Represents raw or processed logs for a workflow run or incident.

Fields:

```text
id
incident_id
workflow_run_id
storage_type
storage_path
raw_content_hash
size_bytes
downloaded_at
created_at
```

Storage options:

```text
database
filesystem
object_storage
```

For early development, storing smaller logs in the database or local files is acceptable.

### LogSection

Represents a relevant extracted section of a log.

Fields:

```text
id
build_log_id
incident_id
job_name
step_name
start_line
end_line
content
section_type
created_at
```

Suggested section types:

```text
error
stack_trace
failed_command
test_failure
dependency_installation
security_scan
docker_build
unknown
```

### AIAnalysis

Represents the output of an AI analysis.

Fields:

```text
id
incident_id
analysis_type
provider
model
prompt_version
status
summary
category
confidence
risk_level
structured_output_json
input_tokens
output_tokens
latency_ms
estimated_cost
error_message
created_at
```

Suggested analysis types:

```text
log_analysis
commit_analysis
fix_generation
model_comparison
```

### AIAnalysisEvidence

Represents evidence used in an AI diagnosis.

Fields:

```text
id
ai_analysis_id
source_type
source_reference
line_start
line_end
message
created_at
```

Source types:

```text
log
diff
commit
workflow
```

### CommitAnalysis

Represents analysis of suspicious commits.

Fields:

```text
id
incident_id
commit_sha
commit_message
author_name
author_email
committed_at
files_changed_count
additions
deletions
root_cause_summary
risk_level
confidence
created_at
```

### PullRequestProposal

Represents a proposed fix before PR creation.

Fields:

```text
id
incident_id
ai_analysis_id
title
description
branch_name
status
risk_level
diff_summary
proposed_changes_json
created_by_user_id
approved_by_user_id
approved_at
created_at
updated_at
```

Suggested status values:

```text
draft
ready_for_review
approved
rejected
pr_created
failed
```

### PullRequest

Represents an actual GitHub Pull Request created by Repo Guardian.

Fields:

```text
id
pull_request_proposal_id
repository_id
github_pr_id
number
title
html_url
branch_name
base_branch
status
created_at
updated_at
```

### LLMRequestLog

Tracks every LLM call.

Fields:

```text
id
incident_id
provider
model
operation
prompt_version
input_tokens
output_tokens
latency_ms
estimated_cost
status
error_message
created_at
```

Operations:

```text
log_analysis
commit_analysis
fix_generation
classification
comparison
```

### Notification

Represents a notification sent or shown to a user.

Fields:

```text
id
user_id
incident_id
type
channel
title
message
status
read_at
sent_at
created_at
```

Channels:

```text
in_app
email
slack
discord
```

## Planned Schema Sequence

The implemented foundation contains:

```text
User
GitHubAccount
Repository
WorkflowRun
BuildJob
Incident
RepositoryConnection
```

Add the remaining entities only with their owning feature, beginning with `WebhookDelivery`:

```text
WebhookDelivery
BuildLog
LogSection
AIAnalysis
PullRequestProposal
LLMRequestLog
Notification
```

## Important Indexes

Recommended indexes:

```text
users.email
github_accounts.github_user_id
repositories.github_repository_id
repositories.full_name
repository_connections.user_id
workflow_runs.github_run_id
workflow_runs.repository_id
workflow_runs.conclusion
incidents.repository_id
incidents.status
incidents.category
webhook_deliveries.github_delivery_id
llm_request_logs.provider
llm_request_logs.model
```

## Data Model Notes

- Avoid storing full provider prompts unless needed; if stored, ensure secrets are redacted.
- Store raw GitHub payloads carefully, because they may contain sensitive metadata.
- Store log excerpts used as AI evidence.
- Keep AI outputs structured to support evaluation.
- Use timestamps consistently.
- Prefer UUIDs for internal IDs if the chosen backend stack supports them cleanly.
