---
applyTo: "backend/**/*.py"
---

# DevPulse Python and FastAPI Instructions

## General Python

- Target the Python version declared by the repository.
- Use type annotations for public functions, methods, and important variables.
- Prefer small, focused functions and explicit names.
- Use timezone-aware UTC timestamps.
- Avoid mutable default arguments.
- Do not suppress exceptions without logging and a clear recovery action.
- Do not introduce a dependency when the standard library or an existing dependency is sufficient. A new dependency goes in the plan and needs the developer's OK.

## Feature-oriented layered structure

Organize FastAPI code by feature, not one global directory per technical layer.

Preferred shape:

```text
app/<feature>/
├── router.py
├── schemas.py
├── service.py
├── repository.py
├── models.py
└── client.py or tasks.py when required
```

Small features may use fewer files. Do not create empty layers.

## FastAPI routers

- Keep routers thin.
- Validate request boundaries with Pydantic.
- Resolve authentication with FastAPI dependencies.
- Call services for use cases.
- Return Pydantic response models.
- Map known application exceptions to safe HTTP responses.
- Never expose stack traces or secrets.
- Do not query SQLAlchemy or GitHub directly.
- Do not return ORM models directly.

## Services

- Put use-case orchestration and business rules in services.
- Enforce ownership in the service and repository query, not only in the frontend.
- Accept internal IDs and validated schemas rather than FastAPI request objects.
- Coordinate repositories, GitHub clients, encryption services, clocks, and task dispatchers.
- Keep service methods transactionally clear.
- Raise typed application exceptions.
- Do not return FastAPI `Response` or `HTTPException` objects from services.

## SQLAlchemy and repositories

- Use SQLAlchemy 2.x style.
- Use explicit sessions and transaction boundaries.
- Use repositories for persistence operations.
- Apply user or connection ownership filters to user-scoped queries.
- Use stable GitHub IDs and unique constraints.
- Implement imports with idempotent upsert behavior where the feature needs it.
- Add indexes for foreign keys, ownership filters, statuses, due schedules, and frequently filtered timestamps when justified.
- Avoid N+1 queries.
- Use bounded pagination for large lists.
- Keep ORM entities separate from API response schemas.

## Alembic

- Create an Alembic migration for every schema change.
- Give migrations descriptive revision messages.
- Validate upgrade behavior.
- Provide safe downgrade behavior when practical.
- Do not edit an already-applied migration to change production history.
- Include unique constraints, indexes, defaults, and nullability explicitly.

## Authentication and sessions

- Use the stable GitHub user ID as the external identity key.
- Prefer opaque server-side DevPulse sessions.
- Store only a secure hash of the session credential.
- Validate session expiration and revocation for protected requests.
- Rotate the session during login to prevent session fixation.
- Set HTTP-only cookies and production `Secure` cookies with the SameSite policy chosen in the spec or plan.
- Never return raw session credentials in API payloads.

## GitHub integration

- Encapsulate GitHub communication in a dedicated client.
- Validate OAuth state and callback correlation.
- Handle pagination explicitly.
- Read and propagate safe rate-limit metadata.
- Convert GitHub errors into internal error types.
- Use short-lived installation access tokens for installation data access.
- Do not store installation tokens as permanent credentials.
- Never log tokens, authorization headers, cookies, private keys, or secrets.
- Do not pass raw GitHub responses beyond the integration boundary.

## Celery

- Celery tasks must be thin entry points into services.
- Pass internal IDs, not tokens or large payloads.
- Make tasks idempotent and safe under duplicate delivery.
- Record user-visible job state in PostgreSQL.
- Use bounded retries with exponential backoff and jitter for retryable failures.
- Do not retry revoked authorization, missing permissions, invalid ownership, or invalid configuration indefinitely.
- Record safe, redacted failure categories.

## Logging and observability

- Use structured logs.
- Include correlation fields such as `request_id`, `connection_id`, `sync_job_id`, `repository_id`, and `delivery_id` when applicable.
- Redact credentials and personal data not required for diagnostics.
- Use appropriate log levels.
- Add metrics for API latency, GitHub failures, sync duration, task failures, and database pool health when the feature requires them.

## Backend testing

Write tests in the same slice as the code. Strict test-first is not required.

- Use Pytest.
- Use service-unit tests with mocked repositories and integration clients.
- Use PostgreSQL integration tests for constraints, transactions, and upserts.
- Use FastAPI integration tests for authentication, validation, response contracts, and ownership.
- Use GitHub fixtures or mocks. Do not call live GitHub from tests.
- Cover the cases that matter for the slice: success, failure, boundaries, ownership, security, idempotency, and retries.
- Use the scenarios in the feature's `spec.md` as the source for test names and cases.
- Never use real credentials in tests.
