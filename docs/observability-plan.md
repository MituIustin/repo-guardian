# Observability Plan

## Goal

Repo Guardian should expose metrics, logs, and dashboards that show the health of the system and the behavior of AI-assisted CI/CD analysis.

Observability is important for both production readiness and dissertation evaluation.

## Tools

Recommended:

```text
Prometheus
Grafana
structured application logs
```

Optional later:

```text
OpenTelemetry
Jaeger
Loki
```

## Metrics Categories

### API Metrics

```text
http_requests_total
http_request_duration_seconds
http_errors_total
```

Labels:

```text
method
route
status_code
```

### GitHub Metrics

```text
github_webhook_events_total
github_webhook_invalid_signatures_total
github_webhook_duplicate_deliveries_total
github_api_requests_total
github_api_errors_total
github_api_rate_limit_remaining
```

Labels:

```text
event_type
repository
status
```

### Workflow Metrics

```text
workflow_runs_total
workflow_runs_failed_total
workflow_runs_succeeded_total
incidents_created_total
open_incidents_total
```

Labels:

```text
repository
branch
workflow
category
severity
```

### Log Processing Metrics

```text
logs_downloaded_total
log_download_failures_total
log_processing_duration_seconds
log_sections_extracted_total
```

### AI Metrics

```text
llm_requests_total
llm_request_duration_seconds
llm_request_failures_total
llm_input_tokens_total
llm_output_tokens_total
llm_estimated_cost_total
ai_analysis_completed_total
ai_analysis_failed_total
```

Labels:

```text
provider
model
operation
status
```

### Queue Metrics

```text
queue_jobs_pending
queue_jobs_running
queue_jobs_completed_total
queue_jobs_failed_total
queue_job_duration_seconds
```

Labels:

```text
queue_name
job_type
```

### Pull Request Metrics

```text
pr_proposals_generated_total
pull_requests_created_total
pull_request_creation_failures_total
```

## Grafana Dashboards

### System Overview

Panels:

- API request rate;
- API error rate;
- average latency;
- service health;
- open incidents;
- failed workflows.

### GitHub Integration Dashboard

Panels:

- webhook events by type;
- invalid signatures;
- duplicate deliveries;
- GitHub API errors;
- rate limit status.

### AI Analysis Dashboard

Panels:

- LLM requests by provider;
- average latency by model;
- estimated cost by model;
- token usage;
- analysis failure rate;
- JSON parsing failure rate.

### Incident Dashboard

Panels:

- incidents by category;
- incidents by severity;
- incidents by repository;
- average time to analysis;
- average time to PR proposal.

### Queue Dashboard

Panels:

- pending jobs;
- failed jobs;
- worker processing time;
- retry count.

### Kubernetes Dashboard

Panels:

- pod status;
- CPU usage;
- memory usage;
- worker replicas;
- restart count.

## Structured Logs

Use structured logs for:

```text
webhook_received
webhook_signature_invalid
workflow_run_stored
incident_created
logs_download_started
logs_download_completed
ai_analysis_started
ai_analysis_completed
pr_proposal_generated
pull_request_created
llm_provider_error
github_api_error
```

Each log should include relevant IDs:

```text
repository_id
workflow_run_id
incident_id
provider
model
delivery_id
```

Do not log:

- access tokens;
- API keys;
- private keys;
- raw secrets;
- full logs containing possible secrets.

## Alerts

Optional alerts:

- high GitHub API error rate;
- high LLM failure rate;
- queue backlog too large;
- worker crash loop;
- invalid webhook signature spike;
- LLM cost above threshold.

## Dissertation Use

Observability can support:

- scalability discussion;
- performance evaluation;
- cost tracking;
- reliability;
- system demonstration;
- comparison of models and providers.
