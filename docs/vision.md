# Repo Guardian Vision

## Product Summary

Repo Guardian is an AI-assisted DevOps platform that helps developers detect, investigate, explain, and resolve failed GitHub Actions builds.

The system receives GitHub webhook events, stores workflow runs and incidents, downloads GitHub Actions logs, extracts relevant error sections, analyzes logs and commits using large language models, classifies the failure type, and can generate safe Pull Request proposals through a GitHub App bot.

## Dissertation Positioning

The project should be presented as more than a dashboard.

Recommended dissertation framing:

> Repo Guardian is an AI-assisted CI/CD incident analysis platform that combines GitHub integration, automated log processing, LLM-based diagnosis, commit analysis, and safe Pull Request generation in a scalable and observable architecture.

## Main Problem

CI/CD failures are often time-consuming to investigate because developers must manually inspect build logs, identify the failing job or step, compare recent commits, understand error patterns, and decide whether the issue is caused by dependencies, tests, configuration, environment, security checks, or code changes.

Repo Guardian addresses this by automatically collecting relevant failure data and presenting an evidence-based AI diagnosis.

## Target Users

- software developers;
- DevOps engineers;
- technical team leads;
- students and researchers studying AI-assisted software engineering;
- teams using GitHub Actions for CI/CD.

## Primary Value

Repo Guardian should reduce the time needed to understand failed builds by:

- detecting failed workflows automatically;
- extracting relevant log sections;
- classifying error types;
- explaining likely causes;
- identifying suspicious commits;
- proposing safe fixes;
- generating Pull Request proposals;
- tracking AI cost and model performance;
- providing a full incident timeline.

## Core End-to-End Scenario

1. A developer pushes code to GitHub.
2. A GitHub Actions workflow fails.
3. GitHub sends a webhook event to Repo Guardian.
4. Repo Guardian stores the workflow run and creates an incident.
5. The system downloads the failed build logs.
6. The log processor extracts relevant error sections.
7. The AI analysis module explains the likely cause.
8. The commit analysis module compares logs with recent code changes.
9. The system classifies the error.
10. The UI displays the diagnosis, evidence, confidence, and recommended action.
11. The user requests a Pull Request proposal.
12. The GitHub App bot creates a branch and opens a Pull Request.
13. Metrics, costs, and model outputs are recorded for evaluation.

## Product Principles

- Human approval is required before creating Pull Requests.
- AI output must be evidence-based and traceable to logs or diffs.
- The interface must clearly separate facts from AI interpretation.
- The system must avoid automatic destructive actions.
- All GitHub and LLM integrations must be testable using mocks.
- The architecture must be suitable for future microservice extraction.
- Documentation must support dissertation writing and defense.

## Non-Goals for Early Development

The first development phase should not focus on:

- complete Kubernetes production hardening;
- multi-cloud deployment;
- billing systems;
- support for GitLab and Bitbucket;
- automatic merge of AI-generated Pull Requests;
- autonomous code modification without user approval;
- enterprise permission models;
- advanced organization analytics.

These can be future work or optional extensions.
