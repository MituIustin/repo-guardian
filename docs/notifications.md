# Notifications Plan

## Goal

Repo Guardian should notify users when important CI/CD and AI analysis events occur.

Notifications should be useful, not noisy.

## Notification Channels

Initial:

```text
in_app
email
```

Future:

```text
slack
discord
webhook
```

## Notification Events

Recommended events:

```text
build_failed
incident_created
logs_downloaded
ai_analysis_completed
ai_analysis_failed
commit_analysis_completed
pr_proposal_ready
pull_request_created
pull_request_creation_failed
high_risk_incident_detected
```

## Notification Preferences

Users should eventually configure:

- channels;
- repositories;
- severity threshold;
- event types;
- quiet hours.

## In-App Notifications

In-app notifications should show:

- title;
- short message;
- related repository;
- related incident;
- timestamp;
- read/unread state;
- action link.

Example:

```text
AI analysis completed
Repo Guardian analyzed the failed CI workflow in owner/repository.
```

## Email Notifications

Email notifications should be concise.

Example:

```text
Subject: Repo Guardian detected a failed workflow in owner/repository

A GitHub Actions workflow failed on branch main.

Workflow: CI
Repository: owner/repository
Incident: CI failed on main
Status: Analysis completed
Probable cause: Dependency error

Open Repo Guardian to review the evidence and recommended action.
```

## Notification Rules

- Do not send duplicate notifications for the same event.
- Do not expose secrets in notifications.
- Do not include full logs in email.
- Include links to Repo Guardian, not raw sensitive content.
- Allow users to disable non-critical notifications.

## Implementation Order

1. Add Notification entity.
2. Add in-app notification API.
3. Add notification center UI.
4. Emit notification for incident creation.
5. Emit notification for analysis completion.
6. Add email provider.
7. Add preferences later.

## Notification Data Model

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

Status values:

```text
pending
sent
failed
read
```

## Testing

Test:

- notification creation;
- duplicate prevention;
- read state update;
- email rendering;
- event-to-notification mapping.
