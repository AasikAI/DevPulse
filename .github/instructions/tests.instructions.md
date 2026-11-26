---
applyTo: "**/{tests,test,__tests__}/**/*"
---

# DevPulse Test Instructions

## Approach

- Write tests in the same slice as the code. Strict test-first is not required, but a slice without tests for its important behavior is not done.
- Use the scenarios and acceptance criteria in the feature's `spec.md` as the source for test names and cases. Name tests after behavior. No requirement-ID bookkeeping is needed.
- Use Given, When, Then organization where it improves readability.
- Do not weaken or delete a test just to make the code pass. If a test is wrong, say so and explain the change.

## Test pyramid

Prefer:

- Many service and rule unit tests
- Focused repository and API integration tests
- Contract tests for GitHub boundaries
- Focused Celery and scheduler tests
- React component tests for user-visible behavior
- A few high-value Playwright journeys

Do not try to prove all behavior through end-to-end tests.

## Cases to consider

Pick the ones that matter for the slice:

- Happy path
- Validation failure and boundary values
- Missing optional data
- Authentication failure
- Authorization and cross-user ownership failure
- Session expiration and revocation
- Idempotency and duplicate delivery
- Partial success
- Retryable and non-retryable errors
- GitHub rate limiting
- Stale data
- Credential redaction
- Database constraints

## Backend unit tests

- Mock repositories, clocks, task dispatchers, encryption services, and GitHub clients at meaningful boundaries.
- Do not mock the unit under test.
- Avoid asserting private implementation calls unless they are a real boundary contract.
- Use deterministic clocks and IDs where time or identity matters.

## PostgreSQL integration tests

Use PostgreSQL integration tests for:

- Unique constraints and foreign keys
- Ownership-scoped queries
- Transactions and rollback
- Idempotent upserts
- Duplicate job protection
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
- Cover what the feature relies on: pagination, missing email, renamed users, selected repositories, suspended installations, removed permissions, rate limits, expired credentials, and transient server errors.
- Do not call live GitHub from tests.
- Never use personal or production credentials.

## Celery and scheduler tests

- Verify that tasks accept internal IDs, not raw credentials.
- Verify duplicate delivery is safe.
- Verify job status transitions and partial success.
- Verify bounded retries and that non-retryable failures stop.
- Verify due configurations are selected correctly.

## Frontend tests

- Use React Testing Library for observable behavior.
- Avoid testing internal component state.
- Cover loading, empty, and error states for each new page, plus other states the feature has.
- Verify that credentials never appear in rendered content or persisted browser storage.

## Playwright tests

Keep end-to-end tests to a few critical journeys of the feature you are building. Use test accounts or controlled mocks. Do not embed credentials in source files.

## Security assertions

Tests involving authentication, GitHub integration, sessions, or synchronization must assert, as applicable:

- Tokens are absent from responses and logs.
- Raw session credentials are not persisted.
- Cookies use the intended security attributes.
- Invalid or reused OAuth state is rejected.
- Cross-user access is denied.
- Duplicate callbacks do not create duplicate records.
- Celery arguments contain no credentials.
- User-visible errors contain no stack traces or sensitive values.
