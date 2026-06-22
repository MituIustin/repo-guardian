# Dissertation Notes

## Possible Dissertation Titles

Recommended titles:

1. AI-Assisted CI/CD Failure Diagnosis and Pull Request Generation Platform
2. Repo Guardian: An AI-Assisted Platform for GitHub Actions Failure Analysis
3. LLM-Based Diagnosis and Remediation Support for CI/CD Pipeline Failures
4. A Scalable Platform for Automated CI/CD Incident Analysis Using Large Language Models
5. AI-Assisted DevOps: Monitoring, Diagnosing, and Repairing Failed GitHub Actions Workflows

## Recommended Main Title

```text
Repo Guardian: An AI-Assisted Platform for GitHub Actions Failure Analysis and Pull Request Proposal Generation
```

## Research Question

Suggested:

```text
How can large language models be integrated into a CI/CD monitoring platform to reduce the effort required to diagnose failed GitHub Actions workflows and generate useful Pull Request proposals?
```

Alternative:

```text
To what extent can LLM-based log and commit analysis improve the diagnosis of CI/CD failures while maintaining human control over code changes?
```

## Dissertation Objective

The objective is to design and implement a platform that monitors GitHub Actions workflows, detects failed builds, analyzes build logs and commits using large language models, classifies failure types, and generates safe Pull Request proposals through a GitHub App bot.

## Main Contributions

Possible contributions:

1. A working platform for monitoring GitHub Actions failures.
2. An automated pipeline for converting failed workflow events into structured incidents.
3. A log processing and evidence extraction mechanism.
4. An LLM abstraction layer for multi-provider analysis.
5. An evidence-based AI diagnosis format.
6. AI-assisted commit analysis.
7. Human-approved Pull Request generation through a GitHub App bot.
8. Cost and latency tracking for LLM providers.
9. Observability dashboards for CI/CD and AI analysis.
10. A model comparison methodology for CI/CD failure diagnosis.

## Proposed Dissertation Structure

### Chapter 1 — Introduction

Content:

- context of CI/CD;
- difficulty of diagnosing failed builds;
- motivation for AI-assisted DevOps;
- project objectives;
- research question;
- dissertation structure.

### Chapter 2 — Background and Related Work

Content:

- CI/CD concepts;
- GitHub Actions;
- build logs and failure diagnosis;
- DevOps automation;
- large language models in software engineering;
- AI-assisted code generation;
- observability;
- Kubernetes and scalable deployment.

### Chapter 3 — Requirements and System Analysis

Content:

- target users;
- functional requirements;
- non-functional requirements;
- security requirements;
- use cases;
- constraints;
- limitations.

### Chapter 4 — System Architecture

Content:

- modular monolith decision;
- module boundaries;
- future microservice extraction;
- data flow;
- deployment architecture;
- background processing;
- queue-based design;
- observability architecture.

### Chapter 5 — Implementation

Content:

- frontend implementation;
- backend API;
- GitHub OAuth;
- webhook processing;
- log download and parsing;
- AI analysis;
- LLM abstraction;
- PR automation;
- tests;
- Kubernetes deployment.

### Chapter 6 — Evaluation

Content:

- dataset;
- evaluation methodology;
- LLM comparison;
- accuracy metrics;
- latency metrics;
- cost metrics;
- qualitative examples;
- system performance;
- discussion.

### Chapter 7 — Conclusions and Future Work

Content:

- achieved objectives;
- limitations;
- future improvements;
- support for GitLab/Bitbucket;
- improved local models;
- stronger static analysis;
- better security redaction;
- enterprise features.

## Important Academic Framing

Avoid presenting the project as a simple CRUD application.

Use this framing:

```text
Repo Guardian combines CI/CD monitoring, automated log processing, LLM-based diagnosis, commit analysis, human-in-the-loop remediation, and scalable observability into a single developer-focused platform.
```

## Evaluation Ideas

Evaluate:

- classification accuracy;
- diagnosis usefulness;
- evidence quality;
- latency;
- cost;
- JSON validity;
- PR proposal usefulness;
- user time reduction;
- user satisfaction.

## Possible Demo Scenario

1. Show GitHub repository.
2. Trigger failing workflow.
3. Show webhook received.
4. Show incident created.
5. Show logs downloaded.
6. Show AI diagnosis.
7. Show commit analysis.
8. Show PR proposal.
9. Approve PR creation.
10. Show created Pull Request.
11. Show metrics in Grafana.

## Limitations to Acknowledge

- AI may produce incorrect diagnoses.
- AI-generated fixes require human review.
- Some logs may not contain enough evidence.
- External LLM providers introduce cost and privacy concerns.
- GitHub API rate limits may affect large-scale usage.
- Model comparison depends on dataset and prompt design.
- Kubernetes deployment is a demonstration, not necessarily production-grade.

## Future Work

Possible future work:

- GitLab and Bitbucket support;
- local LLM deployment;
- advanced static analysis integration;
- secret redaction improvements;
- automatic flaky test detection;
- team collaboration features;
- enterprise RBAC;
- automatic rollback suggestions;
- IDE integration;
- richer model evaluation benchmarks.
