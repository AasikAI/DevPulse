# DevPulse Copilot Instructions

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

Celery, Redis, and the scheduler are part of the approved stack but are **introduced only in the phase whose approved spec includes them**. Do not add, configure, or reference them in code, Docker Compose, or dependencies before that phase.

### Runtime and delivery

- Docker
- Docker Compose
- GitHub Actions
- Structured logging
- OpenTelemetry-compatible observability

Do not introduce Kubernetes, Kafka, microservices, event sourcing, a separate database per module, or a new application framework without explicit approval.

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

The target data flow for GitHub-derived dashboard data is shown below. It is delivered in stages: the connection foundation first, then manual synchronization, and Celery-driven scheduled synchronization in a later phase. Do not build a later stage early.

```text
GitHub
  -> Celery synchronization
    -> Service
      -> Repository
        -> PostgreSQL
          -> FastAPI analytics API
            -> React widgets and charts
```

PostgreSQL is the DevPulse system of record for profile, connection, synchronization, and analytics data. React must not call GitHub directly for dashboard information. Dashboard APIs must read normalized or aggregated data from PostgreSQL.

## Authentication and authorization

- GitHub is the MVP identity provider.
- Do not implement email-and-password authentication.
- Use the stable GitHub user ID as the external identity key.
- Treat DevPulse authentication and GitHub repository authorization as separate states.
- Create a secure DevPulse session after successful GitHub user authorization.
- Prefer opaque server-side sessions backed by PostgreSQL.
- Store only a hash of each session credential.
- Use HTTP-only cookies; production cookies must be Secure and use an approved SameSite policy.
- Validate short-lived, single-use OAuth state.
- Enforce server-side ownership for users, connections, installations, repositories, jobs, and analytics data.
- Request minimum GitHub permissions.

## Credential and secret rules

- Never return GitHub tokens to React.
- Never store credentials in `localStorage` or `sessionStorage`.
- Never place credentials in URLs, query parameters, logs, error responses, or Celery task arguments.
- Keep the GitHub App private key, client secret, webhook secret, and encryption keys outside normal PostgreSQL application tables.
- Generate short-lived installation access tokens when required; do not treat them as permanent credentials.
- Persist a user or refresh token only when an approved feature requires it.
- Encrypt required persisted tokens at application level with keys stored outside PostgreSQL.
- Redact authorization headers, cookies, tokens, and secrets from logs.

## Database rules

- Use PostgreSQL as the system of record.
- Use SQLAlchemy 2.x for persistence.
- Use Alembic for every schema change.
- Use stable GitHub object IDs and database uniqueness constraints where available.
- Make imports and callbacks idempotent.
- Do not expose ORM models directly as API responses.
- Do not create every planned table in the first implementation slice.

## Testing and TDD

Use TDD only after requirements and implementation plans are approved:

1. Write a failing test.
2. Run it and confirm the expected failure.
3. Add the minimum implementation.
4. Run relevant tests.
5. Refactor without changing behavior.
6. Run regression tests.
7. Update traceability.

Use appropriate test levels:

- Service unit tests
- Repository integration tests against PostgreSQL
- PostgreSQL constraint tests
- FastAPI integration tests
- GitHub client contract tests using fixtures or mocks
- Celery task and scheduler tests
- React component tests
- Security tests
- Playwright end-to-end tests

Do not call live GitHub APIs from unit tests. Never place real credentials in fixtures.

## Phase boundaries and source of truth

- Approved specifications under `specs/` are the source of truth for scope. Work only inside the current approved phase.
- Each phase prompt defines that phase's scope and non-goals. Anything listed as a non-goal must not be implemented, stubbed, or exposed in the UI.
- If existing code, a request, or these instructions conflict with an approved spec, stop and report the conflict instead of choosing silently.
- This file is the single source of truth for authentication, session, and credential rules. Path-specific instruction files may apply these rules but must not weaken or contradict them.

## Controlled delivery workflow

For every new feature:

1. Receive intent.
2. Generate `spec.md`, BDD feature files, assumptions, open questions, and coverage.
3. Stop at `AWAITING_REQUIREMENTS_APPROVAL`.
4. Continue only after the exact approval command defined by the feature prompt.
5. Generate design decisions, software design, TDD plan, implementation plan, risks, and traceability.
6. Stop at `AWAITING_IMPLEMENTATION_APPROVAL`.
7. Continue only after the exact implementation approval command.
8. Implement one approved vertical slice at a time using TDD.
9. After each slice, stop at `AWAITING_SLICE_REVIEW`. Do not start the next slice until the human explicitly approves it.

A slice is complete only when:

- Its tests and all existing tests pass
- Requirement and BDD traceability is updated
- No secret appears in logs or responses
- Migrations apply and roll back, when applicable
- Relevant frontend states are covered
- The implementation matches the approved design

Ordinary comments, questions, or review feedback are not approval.

Do not silently:

- Expand scope
- Add dependencies
- Change architecture
- Increase GitHub permissions
- Change credential storage
- Change approved API or database contracts
- Implement a later phase
- Ignore failing tests or security checks

If implementation requires an unapproved deviation, stop and report `IMPLEMENTATION_DEVIATION_REQUIRES_APPROVAL`.