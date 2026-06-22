# AI and LLM Strategy

## Goal

Repo Guardian should use large language models to analyze failed CI/CD builds, explain probable causes, classify error types, analyze suspicious commits, and generate safe Pull Request proposals.

All LLM usage must go through a provider abstraction layer.

## Core AI Tasks

### 1. Log Analysis

Input:

- workflow name;
- failed job;
- failed step;
- relevant log sections;
- repository metadata;
- language/framework if known.

Output:

```json
{
  "summary": "Short explanation of the failure.",
  "category": "dependency_error",
  "confidence": 0.87,
  "riskLevel": "medium",
  "probableCause": "The package installation failed because a dependency version could not be resolved.",
  "evidence": [
    {
      "source": "log",
      "lineStart": 120,
      "lineEnd": 135,
      "message": "npm ERR dependency resolution failed"
    }
  ],
  "recommendedAction": "Review the dependency version in package.json."
}
```

### 2. Commit Analysis

Input:

- log diagnosis;
- changed files;
- commit message;
- diff sections;
- workflow context.

Output:

```json
{
  "suspectedCommit": "commit-sha",
  "rootCauseSummary": "The commit changed dependency versions and introduced an incompatible package.",
  "affectedFiles": ["package.json", "package-lock.json"],
  "confidence": 0.78,
  "riskLevel": "medium",
  "recommendedAction": "Generate a minimal dependency fix proposal."
}
```

### 3. Fix Generation

Input:

- log analysis;
- commit analysis;
- relevant files or diffs;
- constraints.

Output:

```json
{
  "title": "Fix dependency version mismatch in CI",
  "description": "This proposal updates the dependency version to a compatible release.",
  "riskLevel": "medium",
  "changes": [
    {
      "filePath": "package.json",
      "changeType": "modify",
      "explanation": "Updates the package version to a compatible range.",
      "patch": "..."
    }
  ],
  "verificationSteps": [
    "Run npm install.",
    "Run the CI workflow again.",
    "Run the affected test suite."
  ]
}
```

## Error Categories

Use these categories initially:

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

## LLM Provider Abstraction

All provider implementations must follow one common interface.

Conceptual interface:

```text
LLMProvider
  analyzeLogs(input)
  analyzeCommit(input)
  generateFix(input)
  estimateCost(input)
```

Expected providers:

```text
OpenAIProvider
AnthropicProvider
GeminiProvider
LocalProvider
MockProvider
```

## Prompt Versioning

Every prompt must have a version.

Example:

```text
log-analysis-v1
commit-analysis-v1
fix-generation-v1
```

Store prompt version in analysis results.

## Structured Output

Prefer JSON outputs.

Rules:

- validate JSON;
- handle invalid JSON;
- avoid trusting model output blindly;
- store raw output only if safe;
- show parsed structured output in the UI.

## Evidence-Based Diagnosis

AI diagnoses must include evidence.

Evidence can come from:

- log lines;
- stack trace;
- failed command;
- workflow name;
- changed files;
- diff sections;
- commit metadata.

Do not show a diagnosis without evidence if evidence exists.

## Confidence Score

The confidence score should represent model certainty, not truth.

Suggested interpretation:

```text
0.00 - 0.39: low confidence
0.40 - 0.69: medium confidence
0.70 - 0.89: high confidence
0.90 - 1.00: very high confidence
```

The UI should show uncertainty clearly.

## Cost Tracking

For every LLM request, record:

```text
provider
model
operation
input_tokens
output_tokens
latency_ms
estimated_cost
status
error_message
```

## Log Reduction Strategy

Do not send entire logs blindly.

Steps:

1. parse logs;
2. identify failed job and step;
3. extract relevant sections;
4. include surrounding context;
5. redact secrets;
6. truncate safely;
7. include structured metadata.

## Safety Rules

- Do not allow AI to create PRs without user approval.
- Do not allow AI to merge PRs.
- Do not allow AI to push to the default branch.
- Show AI uncertainty.
- Show evidence.
- Keep generated changes minimal.
- Prefer safe fixes over broad refactors.
- Flag high-risk suggestions.

## Mock Provider

The mock provider is required for tests.

It should return deterministic outputs for fixture logs.

Purpose:

- stable tests;
- no real API cost;
- no dependency on provider uptime;
- reproducible evaluation.

## LLM Failure Handling

Handle:

- provider timeout;
- rate limit;
- invalid API key;
- invalid JSON output;
- unsafe output;
- empty output;
- excessive token input;
- unsupported model.

## Dissertation Relevance

This AI layer is one of the main academic contributions.

It supports discussion of:

- AI-assisted software engineering;
- CI/CD failure diagnosis;
- explainability;
- human-in-the-loop automation;
- model comparison;
- cost-performance tradeoffs;
- limitations of LLM-generated fixes.
