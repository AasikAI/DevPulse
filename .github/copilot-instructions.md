# DevPulse Copilot Instructions

## How we work

DevPulse is built by one developer who uses Copilot as an assistant. Copilot helps; the developer designs, reviews, and decides. The developer is also using this project to strengthen their fullstack skills, so keep changes small and readable, and explain non-obvious choices in a sentence or two in your summaries.

There are no fixed phases. Features can be built in any order or in parallel. Every feature follows the same loop:

```text
intent -> spec -> plan -> MVP slice -> review -> UI/UX pass -> fix -> iterate
```

### The loop

1. **Intent.** The developer describes what they want in plain words.
2. **Spec.** The intent becomes one file, `specs/<feature>/spec.md`, with: the intent in the developer's words, goal and scope, non-goals, technical notes (data, API, background jobs, security), scenarios in Given/When/Then form, acceptance criteria, and a short list of open questions and assumptions. Do not create separate files for scenarios, assumptions, coverage, or traceability unless asked. If a request is more than a small change and has no spec, draft one in this format and ask the developer to review it before planning.
3. **Plan.** Before writing code, write a short plan in the chat: the slices in order (the first slice is the smallest working end-to-end MVP), the modules and files you expect to touch, new dependencies, schema changes, and risks. Then **stop and wait** for the developer.
4. **MVP slice.** Build one working slice at a time: code, tests, and any migration together. Rough is fine; working end to end is required.
5. **Review.** After each slice, **stop and wait**. Give a summary: what changed, how to run it, how to test it, anything that differs from the spec or plan, and open questions.
6. **UI/UX pass, fix, iterate.** The developer reviews, asks for UI/UX improvements and fixes, and the next slice or iteration starts only when they say so.

A question or comment from the developer is a question, not permission to continue to the next slice. Answer it, then wait.

### A slice is done when

- The happy path works end to end.
- Its tests and the existing tests pass.
- No secret appears in logs or responses.
- Any migration applies cleanly.
- New pages have loading, empty, and error states. Visual polish can wait for the UI/UX pass.

### Ask before you

- Add a dependency.
- Change the architecture or the layer rules.
- Increase GitHub permissions.
- Change how credentials are stored.
- Change an API or database contract agreed in the spec.
- Add scope that the spec does not mention.
- Delete or rewrite files outside the feature you are working on.

If the spec is ambiguous, ask a short question instead of guessing. If the code, a request, or these instructions conflict with the spec, say so and ask. Anything the spec lists as a non-goal must not be implemented, stubbed, or exposed in the UI.

## Product context

DevPulse is a personal engineering intelligence dashboard that transforms authorized GitHub data into visual insights about development activity, technologies, pull requests, reviews, repositories, and CI/CD reliability.

DevPulse is not:

- An employee-monitoring product
- A developer-ranking system
- A productivity-scoring system
- A platform for comparing developers
- A source-code storage platform

Use neutral, evidence-based language. Do not infer productivity or skill from commit counts, pull-request counts, or technology detections.

## Approved technology stack

### Frontend

- React
- TypeScript
- Vite
- React Router
- Tailwind CSS
- Apache ECharts
- Vitest
- React Testing Library
- Playwright

### Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy 2.x
- Alembic
- Pytest

### Data and background processing

- PostgreSQL
- Celery
- Redis
- Celery Beat or an approved scheduler

Introduce Celery, Redis, and the scheduler when a feature needs background or scheduled work, add them through Docker Compose, and mention them in the plan.

### Runtime and delivery

- Docker
- Docker Compose
- GitHub Actions
- Structured logging
- OpenTelemetry-compatible observability

Do not introduce Kubernetes, Kafka, microservices, event sourcing, a separate database per module, or a new application framework without asking first.

## Architecture

DevPulse uses a **feature-oriented layered modular-monolith architecture**.

The FastAPI backend is one application and one codebase organized by business feature. Initial modules may include:

- `identity`
- `profile`
- `github_integration`
- `tool_configuration`
- `repositories`
- `synchronization`
- `development_activity`
- `technologies`
- `pull_requests`
- `cicd`
- `analytics`
- `insights`

Within a feature, use these layers where applicable:

```text
Router
  -> Service
    -> Repository or integration client
      -> PostgreSQL, GitHub, Redis, or another infrastructure dependency
```

Keep the design practical. Do not add interfaces, abstractions, factories, or layers unless they enforce a meaningful boundary or improve testability.

## Layer rules

### Router

Routers may:

- Accept and validate HTTP input
- Resolve the authenticated user
- Call a service
- Map application results to API responses
- Map known application errors to safe HTTP errors

Routers must not:

- Query SQLAlchemy directly
- Call GitHub directly
- Contain business rules
- Calculate analytics
- Implement synchronization logic

### Service

Services must:

- Implement application use cases
- Enforce business and ownership rules
- Coordinate repositories and external clients
- Define transaction boundaries when appropriate
- Raise application-specific exceptions

### Repository

Repositories must:

- Perform SQLAlchemy persistence
- Apply user and connection ownership conditions
- Support idempotent upserts where required
- Keep persistence details out of services and routers

Repositories must not:

- Call GitHub
- Dispatch Celery jobs
- Return FastAPI responses
- Make UI decisions

### External integration client

The GitHub client must:

- Encapsulate GitHub API communication
- Handle pagination
- Read rate-limit information
- Convert GitHub errors into internal errors
- Generate installation access tokens when required
- Convert GitHub responses into internal schemas

Do not propagate raw GitHub responses throughout the application.

### Celery task

Celery tasks are background entry points into application services.

```text
Celery task -> Service -> GitHub client and repositories
```

Celery tasks must not duplicate business logic from services. Pass internal identifiers such as `connection_id` and `sync_job_id`, not raw credentials.

## Allowed dependency flow

```text
React -> FastAPI API
FastAPI router -> Service
Celery task -> Service
Service -> Repository
Service -> GitHub client
Repository -> SQLAlchemy
GitHub client -> GitHub API
Analytics service -> Analytics repository
```

Do not allow:

```text
React -> GitHub API
Router -> SQLAlchemy
Router -> GitHub API
Repository -> GitHub API
Repository -> Celery
Celery task -> duplicated business logic
Dashboard endpoint -> live GitHub fetch on every request
Feature router -> another feature's repository
```

## Data-flow rule

GitHub-derived dashboard data always flows through the database:

```text
GitHub
  -> Celery synchronization
    -> Service
      -> Repository
        -> PostgreSQL
          -> FastAPI analytics API
            -> React widgets and charts
```

PostgreSQL is the DevPulse system of record for profile, connection, synchronization, and analytics data. React must not call GitHub directly for dashboard information. Dashboard APIs must read normalized or aggregated data from PostgreSQL, never fetch from GitHub on each request.

A feature may start with a simpler way to fetch data (for example a manual trigger) while building the MVP, as long as the data still goes through the service, repository, and database.

## Authentication and authorization

- GitHub is the MVP identity provider.
- Do not implement email-and-password authentication.
- Use the stable GitHub user ID as the external identity key.
- Treat DevPulse authentication and GitHub repository authorization as separate states.
- Create a secure DevPulse session after successful GitHub user authorization.
- Prefer opaque server-side sessions backed by PostgreSQL.
- Store only a hash of each session credential.
- Use HTTP-only cookies; production cookies must be Secure and use a SameSite policy chosen in the spec or plan.
- Validate short-lived, single-use OAuth state.
- Enforce server-side ownership for users, connections, installations, repositories, jobs, and analytics data.
- Request minimum GitHub permissions.

## Credential and secret rules

These rules are always on, even for an MVP. This file is the single source of truth for authentication, session, and credential rules. Path-specific instruction files may apply these rules but must not weaken them.

- Never return GitHub tokens to React.
- Never store credentials in `localStorage` or `sessionStorage`.
- Never place credentials in URLs, query parameters, logs, error responses, or Celery task arguments.
- Keep the GitHub App private key, client secret, webhook secret, and encryption keys outside normal PostgreSQL application tables.
- Generate short-lived installation access tokens when required; do not treat them as permanent credentials.
- Persist a user or refresh token only when the spec explicitly requires it.
- Encrypt required persisted tokens at application level with keys stored outside PostgreSQL.
- Redact authorization headers, cookies, tokens, and secrets from logs.

## Database rules

- Use PostgreSQL as the system of record.
- Use SQLAlchemy 2.x for persistence.
- Use Alembic for every schema change.
- Use stable GitHub object IDs and database uniqueness constraints where available.
- Make imports and callbacks idempotent.
- Do not expose ORM models directly as API responses.
- Create only the tables the current slice needs.

## Testing

Write tests together with the code, in the same slice. Strict test-first is not required, but a slice without tests for its important behavior is not done.

Cover what matters for the slice:

- Business rules and ownership in services
- Database behavior that depends on PostgreSQL (constraints, upserts, transactions)
- API behavior: validation, authentication, ownership, safe errors
- GitHub client behavior using fixtures or mocks
- Background tasks: duplicate delivery, retries, and failure handling
- Key UI behavior with React Testing Library, and a few key journeys with Playwright

Use the scenarios in the spec as the source for test names and cases. Do not call live GitHub APIs from tests. Never place real credentials in fixtures.