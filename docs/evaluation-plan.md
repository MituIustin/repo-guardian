# Evaluation Plan

## Goal

Evaluate Repo Guardian from both technical and AI-assisted diagnosis perspectives.

The evaluation should show that the system is functional, useful, measurable, and suitable for dissertation presentation.

## Evaluation Dimensions

### 1. Functional Evaluation

Verify that the end-to-end workflow works:

```text
GitHub workflow failure
→ webhook received
→ workflow run stored
→ incident created
→ logs downloaded
→ logs parsed
→ AI diagnosis generated
→ commit analyzed
→ PR proposal generated
→ PR created after approval
```

### 2. AI Evaluation

Evaluate model outputs for:

- error classification accuracy;
- root cause quality;
- evidence quality;
- JSON validity;
- hallucination rate;
- fix usefulness;
- cost;
- latency.

### 3. System Evaluation

Evaluate:

- API response time;
- background job processing time;
- log processing time;
- queue behavior;
- worker scaling;
- observability metrics;
- Kubernetes deployment behavior.

### 4. UX Evaluation

Evaluate whether users can understand and use the system.

Possible user tasks:

1. Find a failed build.
2. Identify probable cause.
3. Review log evidence.
4. Review AI diagnosis.
5. Generate a PR proposal.
6. Decide whether to create the PR.

Possible questionnaire items:

- The system helped me understand the failed build faster.
- The AI diagnosis was clear.
- The evidence shown was useful.
- The Pull Request proposal was understandable.
- I would trust the system only with human approval.
- The interface was easy to navigate.

## Evaluation Dataset

Create 30 to 50 incidents.

Categories:

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

Each incident should have:

```text
workflow payload
log file
expected category
expected root cause
relevant lines
changed files
expected fix type
difficulty level
```

## Quantitative Metrics

### AI Metrics

```text
classification_accuracy
json_validity_rate
average_latency_ms
average_cost
average_input_tokens
average_output_tokens
hallucination_rate
```

### System Metrics

```text
webhook_processing_time
log_download_time
log_parsing_time
ai_analysis_time
pr_creation_time
queue_wait_time
```

### UX Metrics

```text
task_completion_rate
average_task_time
user_confidence_score
perceived_usefulness_score
```

## Qualitative Evaluation

Include examples of:

- a correct AI diagnosis;
- a partially correct diagnosis;
- an incorrect diagnosis;
- a useful PR proposal;
- a risky PR proposal that requires human judgment.

## Model Comparison

Compare at least two providers or models if time allows.

Suggested dimensions:

```text
accuracy
cost
latency
evidence quality
fix usefulness
structured output reliability
```

## Expected Dissertation Results

The evaluation should support statements such as:

```text
Repo Guardian successfully processes failed GitHub Actions workflows and transforms them into structured incidents enriched with log evidence and AI-generated explanations.
```

and:

```text
The model comparison shows tradeoffs between cost, latency, and diagnosis quality.
```

Avoid unsupported claims such as:

```text
The system always finds the correct fix.
```

## Limitations

Acknowledge:

- dataset size;
- limited repository diversity;
- subjectivity in manual scoring;
- LLM non-determinism;
- provider changes over time;
- privacy concerns when sending logs to external providers;
- not all build failures can be safely fixed automatically.
