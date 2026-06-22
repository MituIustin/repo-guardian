# Frontend Plan

## Goal

Transform the current mocked UI into a clean, production-oriented developer tool.

The frontend should initially support mock data where needed, but it must be structured so mock data can be replaced with backend API calls without major rewrites.

## Recommended Stack

Use the existing stack if it is already reasonable.

Preferred frontend options:

- React;
- TypeScript;
- Vite or Next.js;
- React Router or Next routing;
- TanStack Query for server state;
- a clean component structure;
- CSS modules, Tailwind, or another consistent styling approach.

Avoid changing the stack unless there is a clear reason.

## Folder Structure

Recommended structure:

```text
apps/frontend/
  src/
    app/
    api/
    components/
    features/
      auth/
      dashboard/
      repositories/
      incidents/
      workflow-runs/
      ai-analysis/
      pull-requests/
      settings/
    layouts/
    mocks/
    routes/
    styles/
    types/
    utils/
```

## Feature-Based Structure

Each major feature should own:

```text
components
api
types
hooks
utils
```

Example:

```text
features/incidents/
  api/
  components/
  hooks/
  types.ts
  utils.ts
```

## Frontend Development Order

### Step 1 — Audit Existing UI

Identify:

- current screens;
- mock data files;
- reusable components;
- inconsistent terminology;
- unclear labels;
- layout issues;
- components worth keeping;
- components worth replacing.

### Step 2 — Define Design System Basics

Create reusable primitives:

- Button;
- Card;
- Badge;
- Table;
- Tabs;
- Select;
- SearchInput;
- EmptyState;
- LoadingState;
- ErrorState;
- CodeBlock;
- DiffViewer;
- Timeline;
- MetricCard.

### Step 3 — Redesign Layout

Create:

- authenticated app layout;
- sidebar or top navigation;
- page header pattern;
- content container;
- responsive structure.

### Step 4 — Rebuild Dashboard

Dashboard should include:

- high-level repository health;
- failed workflow count;
- open incidents;
- PR proposals;
- recent incident timeline;
- LLM cost summary.

### Step 5 — Rebuild Repositories Page

Requirements:

- repository list;
- filters;
- search;
- branch status;
- latest workflow status;
- incident count.

### Step 6 — Rebuild Incidents Page

Requirements:

- incident list;
- status filters;
- severity filters;
- category filters;
- clear incident cards or table;
- useful empty state.

### Step 7 — Rebuild Incident Details

Requirements:

- incident header;
- workflow metadata;
- log evidence;
- AI diagnosis;
- commit analysis;
- PR proposal area;
- timeline.

### Step 8 — Add API Layer

Create a central API client.

Do not call `fetch` randomly inside components.

Recommended:

```text
src/api/client.ts
src/features/incidents/api/incidentsApi.ts
src/features/repositories/api/repositoriesApi.ts
```

### Step 9 — Replace Mocks Gradually

Replace mock data per feature:

1. repositories;
2. workflow runs;
3. incidents;
4. logs;
5. AI analyses;
6. PR proposals.

## Frontend Rules

- Use English everywhere.
- Do not use emojis.
- Avoid hardcoded fake data in production paths.
- Keep components small.
- Keep visual language consistent.
- Do not use unclear labels.
- Do not overuse animations.
- Use animations only for meaningful loading or progress states.
- Use accessible labels and focus states.

## Important Screens for Dissertation Demo

The demo should show:

1. GitHub login.
2. Connected repository dashboard.
3. Failed build incident.
4. Extracted log evidence.
5. AI diagnosis.
6. Commit analysis.
7. PR proposal.
8. PR creation result.
9. Metrics/cost tracking.
10. Observability dashboard.

## UI Copy Examples

Good:

```text
Analyze failed build
View log evidence
Generate PR proposal
Create Pull Request
Analysis completed
Webhook verified
```

Bad:

```text
Fix everything
AI magic
Boom
Something broke
Smart repair
```

## Frontend Testing

Add:

- component tests for important components;
- integration tests for pages;
- E2E tests for main flows.

E2E flows:

```text
login
connect repository
view failed incident
run AI analysis
review PR proposal
create PR
```
