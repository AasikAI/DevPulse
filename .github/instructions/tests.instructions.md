---
applyTo: "**/{tests,test,__tests__}/**/*"
---

# DevPulse Test Instructions

## Approval and traceability

- Write implementation tests only for approved requirements and approved implementation slices.
- Trace every test to a requirement ID and, where applicable, a BDD feature and scenario.
- Keep test names behavior-focused.
- Use Given, When, Then organization where it improves readability.
- Do not weaken or delete an approved test merely to make an implementation pass.

## TDD loop

For each approved slice:

1. Add the smallest meaningful failing test.
2. Run it and confirm that it fails for the expected reason.
3. Add the minimum implementation.
4. Run focused tests.
5. Refactor.
6. Run relevant regression tests.
7. Update traceability.
8. Stop for slice review.

Do not write tests, fixtures, or mocks for functionality that belongs to a later phase or is listed as a non-goal of the current approved spec.

## Test pyramid

Prefer:

- Many service and rule unit tests
- Focused repository and API integration tests
- Contract tests for GitHub boundaries
- Focused Celery and scheduler tests
- React component tests for user-visible behavior
- A small number of high-value Playwright journeys

Do not attempt to prove all behavior through end-to-end tests.

## Required scenario categories

Include applicable tests for:

- Happy path
- Validation failure
- Boundary values
- Missing optional data
- Authentication failure
- Authorization and ownership failure
- Session expiration and revocation
- Idempotency and duplicate delivery
- Partial success
- Retryable and non-retryable errors
- GitHub rate limiting
- Stale data
- Credential redaction
- Cross-user isolation
- Database constraints

## Backend unit tests

- Mock repositories, clocks, task dispatchers, encryption services, and GitHub clients at meaningful boundaries.
- Do not mock the unit under test.
- Avoid asserting private implementation calls unless they represent an approved boundary contract.
- Use deterministic clocks and IDs where time or identity matters.

## PostgreSQL integration tests

Use PostgreSQL integration tests for:

- Unique constraints
- Foreign keys
- Ownership-scoped queries
- Transactions and rollback
- Idempotent upserts
- Concurrent or duplicate job protection
- Migration upgrade behavior

Do not rely only on SQLite when PostgreSQL-specific behavior matters.

## FastAPI integration tests

Cover:

- Request validation
- Authentication dependencies
- Authorization and ownership
- Cookie behavior
- Response schemas
- Safe errors
- No credential leakage

## GitHub contract tests

- Use representative GitHub fixtures or mocked responses.
- Cover pagination, missing email, renamed users, selected repositories, suspended installations, removed permissions, rate limits, expired credentials, and transient server errors.
- Do not call live GitHub from unit or normal CI tests.
- Never use personal or production credentials.

## Celery and scheduler tests

- Verify that tasks accept internal IDs, not raw credentials.
- Verify duplicate delivery is safe.
- Verify job status transitions.
- Verify partial success is preserved.
- Verify bounded retry and backoff decisions.
- Verify non-retryable failures stop.
- Verify due configurations are selected correctly.

## Frontend tests

- Use React Testing Library for observable behavior.
- Avoid testing internal component state.
- Cover loading, success, empty, stale, partial, permission, rate-limit, and error states.
- Verify that credentials never appear in rendered content or persisted browser storage.

## Playwright tests

Keep end-to-end tests limited to critical journeys that belong to the current approved phase.

Phase 2 journey (GitHub authentication and connection):

```text
Continue with GitHub
-> Restore session
-> View profile
-> Configure GitHub installation
-> View connected status
-> Disconnect GitHub (DevPulse session preserved)
-> Log out
```

Eventual MVP journey (illustrative only; do not write tests for these steps until the phase that approves them):

```text
Continue with GitHub
-> Restore session
-> View profile
-> Configure GitHub installation
-> Select repository
-> Start synchronization
-> View PostgreSQL-backed dashboard data
```

Use test accounts or controlled mocks. Do not embed credentials in source files.

## Security assertions

Tests involving authentication, GitHub integration, sessions, or synchronization must assert as applicable:

- Tokens are absent from responses.
- Tokens are absent from logs.
- Raw session credentials are not persisted.
- Cookies use approved security attributes.
- Invalid or reused state is rejected.
- Cross-user access is denied.
- Duplicate callbacks do not create duplicate records.
- Celery arguments contain no credentials.
- User-visible errors contain no stack traces or sensitive values.