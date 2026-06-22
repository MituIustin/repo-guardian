# LLM Evaluation Plan

## Goal

Evaluate how well different LLM providers and models diagnose CI/CD failures and generate useful fix proposals.

The evaluation should be suitable for a dissertation chapter.

## Evaluation Questions

1. How accurately can LLMs classify CI/CD failure types?
2. How useful are LLM-generated explanations?
3. How often do models provide evidence from logs?
4. How often do models produce valid structured JSON?
5. How costly is each model?
6. How fast is each model?
7. How useful are generated Pull Request proposals?
8. Which model offers the best cost-quality tradeoff?

## Dataset

Create a dataset of failed workflow incidents.

Suggested size:

```text
30 to 50 incidents
```

Suggested distribution:

```text
10 dependency errors
10 test failures
5 lint errors
5 Docker errors
5 missing secret errors
5 configuration errors
5 syntax errors
5 unknown or ambiguous failures
```

The dataset can include:

- real failed builds from test repositories;
- controlled artificial repositories;
- fixture logs;
- manually created failure cases.

## Ground Truth

For every incident, store:

```text
incident_id
repository
workflow
correct_category
correct_root_cause
relevant_log_lines
relevant_files
expected_fix_type
difficulty_level
```

## Metrics

### Classification Accuracy

Measures whether the model selected the correct error category.

```text
correct classifications / total incidents
```

### Root Cause Quality

Manual score from 1 to 5.

```text
1 = incorrect
2 = mostly incorrect
3 = partially correct
4 = mostly correct
5 = correct and useful
```

### Evidence Quality

Manual score from 1 to 5.

```text
1 = no evidence
2 = vague evidence
3 = somewhat relevant evidence
4 = relevant evidence
5 = precise evidence with lines/files
```

### JSON Validity Rate

Percentage of model outputs that match the expected schema.

```text
valid JSON outputs / total outputs
```

### Latency

Average response time per model.

```text
average latency in milliseconds
```

### Cost

Estimated cost per analysis.

```text
input cost + output cost
```

### Fix Usefulness

Manual score from 1 to 5.

```text
1 = harmful or unrelated
2 = unlikely to help
3 = partially useful
4 = useful
5 = directly applicable
```

### Hallucination Rate

Percentage of outputs that invent files, errors, or facts not present in logs or diffs.

## Model Comparison Table

Example:

```text
Model | Accuracy | Avg Latency | Avg Cost | JSON Validity | Evidence Quality | Fix Usefulness
```

## Evaluation Workflow

1. Select incident fixture.
2. Run log analysis with each model.
3. Store structured output.
4. Run commit analysis with each model.
5. Store structured output.
6. Optionally run fix generation.
7. Compare output against ground truth.
8. Calculate metrics.
9. Generate charts.
10. Discuss results.

## Evaluation Storage

Store:

```text
evaluation_runs
evaluation_cases
evaluation_outputs
evaluation_scores
```

## Bias and Limitations

Acknowledge:

- small dataset size;
- limited project diversity;
- possible manual scoring subjectivity;
- prompts may favor some models;
- provider versions may change;
- real-world logs may contain secrets or noise;
- not all failures have safe automatic fixes.

## Dissertation Output

The evaluation chapter should include:

- dataset description;
- methodology;
- metrics;
- results table;
- charts;
- qualitative examples;
- limitations;
- conclusions.

## Important Rule

Do not claim that a model is objectively best in all cases.

Use wording such as:

```text
In this evaluation dataset, Model A achieved the best classification accuracy, while Model B offered lower latency and lower estimated cost.
```
