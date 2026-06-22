# UI Redesign Plan

## Context

The existing Repo Guardian UI is a mocked prototype. It can be changed as much as needed.

The new UI should look like a serious developer tool, not a generic student dashboard.

All UI text must be in English. Do not use emojis.

## Product Tone

The interface should be:

- technical;
- clean;
- focused;
- professional;
- precise;
- calm;
- readable.

Avoid:

- playful language;
- emojis;
- vague labels;
- excessive gradients;
- decorative cards without purpose;
- inconsistent status colors;
- crowded dashboards.

## Main Screens

### 1. Login Screen

Purpose:

- introduce Repo Guardian briefly;
- allow GitHub login;
- explain what the app does in one sentence.

Suggested copy:

```text
Repo Guardian monitors GitHub Actions builds, analyzes CI/CD failures, and helps generate safe Pull Request proposals.
```

Main action:

```text
Continue with GitHub
```

### 2. Dashboard

Purpose:

- provide overview of repositories, failed builds, incidents, and AI analysis status.

Important widgets:

- connected repositories count;
- failed workflows in the last 24 hours;
- open incidents;
- PR proposals ready for review;
- LLM cost this month;
- recent incidents timeline.

Avoid showing too many metrics early.

### 3. Repository List

Purpose:

- show monitored repositories and build health.

Columns or card fields:

- repository name;
- monitored branch;
- latest workflow status;
- open incidents;
- last analysis;
- last build time;
- actions.

Filters:

- status;
- branch;
- owner;
- open incidents;
- search.

### 4. Repository Details

Purpose:

- show workflow activity for one repository.

Sections:

- repository summary;
- monitored branch;
- latest workflow runs;
- open incidents;
- webhook status;
- GitHub App installation status.

### 5. Incidents Page

Purpose:

- list failed builds that need investigation.

Filters:

- repository;
- severity;
- category;
- status;
- model/provider;
- date range.

Each incident item should show:

- title;
- repository;
- workflow;
- failed job;
- category;
- severity;
- confidence;
- status;
- created time.

### 6. Incident Details Page

This is the most important screen.

Recommended sections:

1. Incident Header
2. Workflow Summary
3. Failure Timeline
4. Relevant Log Sections
5. AI Diagnosis
6. Commit Analysis
7. Suggested Fix
8. Pull Request Proposal
9. Activity and Audit Log

The page should clearly separate:

- facts from GitHub;
- extracted log evidence;
- AI interpretation;
- proposed changes;
- user-approved actions.

### 7. AI Diagnosis Panel

Must include:

- summary;
- category;
- confidence;
- risk level;
- evidence lines;
- likely cause;
- recommended next action;
- model/provider used;
- latency;
- estimated cost.

Do not present AI output as guaranteed truth.

Use labels like:

```text
Probable cause
Evidence
Recommended action
Confidence
Model
Cost estimate
```

### 8. Commit Analysis Panel

Must include:

- suspected commit;
- changed files;
- reasoning;
- relation to log evidence;
- risk level;
- confidence.

### 9. Pull Request Proposal Page

Must include:

- proposal title;
- generated PR description;
- changed files;
- diff viewer;
- risk level;
- verification steps;
- approval button;
- create PR button.

Important:

The user must approve before PR creation.

### 10. Settings

Sections:

- GitHub connection;
- connected repositories;
- LLM provider settings;
- notification preferences;
- cost limits;
- webhook status.

## Visual Hierarchy

Use clear hierarchy:

1. page title;
2. summary metrics;
3. primary content;
4. supporting metadata;
5. secondary actions.

Avoid putting all information at the same visual weight.

## Status Labels

Use consistent status vocabulary:

Workflow status:

```text
Queued
In Progress
Succeeded
Failed
Cancelled
Skipped
```

Incident status:

```text
Open
Investigating
Analysis Completed
PR Proposed
PR Created
Resolved
Ignored
```

Analysis status:

```text
Not Started
Queued
Running
Completed
Failed
```

Risk level:

```text
Low
Medium
High
Critical
```

## Empty States

Every major page should have a useful empty state.

Examples:

Repository list:

```text
No repositories connected yet.
Connect a GitHub repository to start monitoring workflow runs.
```

Incidents:

```text
No open incidents.
Repo Guardian will create incidents automatically when monitored workflows fail.
```

AI Analysis:

```text
No AI analysis has been generated yet.
Run analysis after logs are available.
```

## Loading States

Use loading states for:

- GitHub login callback;
- repository loading;
- webhook status checks;
- log download;
- AI analysis;
- Pull Request creation.

Do not block the full application unless needed.

## Error States

Show clear errors for:

- GitHub authorization failure;
- missing GitHub App installation;
- webhook verification failure;
- GitHub API rate limit;
- log download failure;
- LLM provider failure;
- PR creation failure.

## Code Diff Viewer

The diff viewer must be large and readable.

Requirements:

- file list;
- changed lines;
- additions and deletions;
- non-contiguous diff support;
- line numbers;
- clear visual separation between files.

## Progressive Disclosure

Do not show all technical data immediately.

Recommended approach:

- show summary first;
- allow expanding logs;
- allow expanding raw AI output;
- allow expanding raw webhook payload only in developer/debug mode.

## Mock Data Removal Strategy

The UI may keep mock data during early development, but it must be clearly separated.

Recommended folders:

```text
src/mocks
src/api
src/features
```

Rules:

- mock data must not be mixed into production API clients;
- each mocked screen should have a clear path to real API data;
- once backend endpoints exist, replace mocks gradually.

## Accessibility

Minimum requirements:

- readable contrast;
- visible focus states;
- keyboard-accessible buttons;
- labels for inputs;
- no color-only status communication;
- responsive layout.

## No Emoji Rule

Do not use emojis in:

- UI labels;
- notifications;
- status tags;
- commit messages;
- documentation;
- console logs;
- generated PR descriptions.

## Recommended Navigation

The implemented foundation uses this top-level navigation:

```text
Overview
Repositories
Builds
Incidents
Settings
```

Optional later:

```text
Observability
Cost Tracking
Evaluation
```

## Implemented Repository Experience

The repository screen uses the authenticated GitHub and backend connection APIs. It presents GitHub accounts and organizations as separate repository sources, supports automatic synchronization, deliberate reconnection, per-source and global disconnection, compact repository search, individual disconnection, and monitored-branch selection. Repository counts and webhook status reload from authoritative API state after live WebSocket notifications. Workflow reruns and failure evidence remain in Builds to keep repository management focused.

The manual repository flow follows a strict source, repository, branch sequence. Account disconnection is visually separated from reversible repository disconnection and explains that the GitHub App will be uninstalled.

The Builds screen is repository-first. It separates owner and repository identity, summarizes latest repository health, supports search plus repository and status filters, shows one latest run per repository by default, and progressively reveals history, jobs, steps, error evidence, links, and rerun actions.

The previous last-build mock has been removed. Signed-out users receive an authentication message instead of fabricated repository or metric content.

## Implemented Build Monitoring Experience

The Builds page uses persisted API data and an authenticated WebSocket stream. It includes running, failed, and passed filters; workflow, branch, commit, trigger, update time, job links, the GitHub Actions run link, and expandable error evidence.
