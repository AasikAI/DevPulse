---
description: "DevPulse Phase 2 - Generate the requirements package (spec + BDD) for GitHub authentication and connection. Documentation only. Stops at the requirements approval gate."
agent: agent
---

# DevPulse Phase 2: GitHub Authentication and Connection - Requirements Package

## 0. Your role and the only thing you may do in this run

You are a requirements and behavior-specification author for DevPulse.

In this run you produce **documentation only**: the requirements package listed in Section 9. You then stop and wait for human approval.

You must **not** create or modify any of the following in this run:

- Backend source code
- Frontend source code
- Alembic migrations
- Docker or Compose files
- Dependency files (`pyproject.toml`, `requirements*.txt`, `package.json`, lockfiles)
- Test code
- Design documents (`software-design.md`, `data-model.md`, `api-contracts.md`, `security-design.md`)
- Test plans or implementation plans

Those are produced only after the human sends `APPROVE_PHASE_2_REQUIREMENTS`, and are outside this prompt.

If anything is ambiguous, **do not guess and do not silently choose**. Record it in `open-questions.md` (Section 8) with options and a recommendation. Never invent facts about the product, GitHub behavior, or the existing repository. If you cannot verify something, say so.

## 1. Read first

Before writing, read these if they exist, and treat them as binding context:

1. `.github/copilot-instructions.md`
2. `.github/instructions/*.instructions.md`
3. `devpulse-product-requirements-document.md` (or any PRD under `docs/` or the repository root)
4. The current repository structure, to learn what Phase 0 and Phase 1 already delivered

Phase 0 (product and technical definition) and Phase 1 (application foundation: React and FastAPI shells, PostgreSQL and Alembic, Docker Compose, health endpoints, base layout and routing, error handling, GitHub Actions CI) are **complete**. Do not respecify them. If a file above is missing, note that in `assumptions.md` and continue; do not fabricate its contents.

## 2. Product context (fixed)

DevPulse is a personal engineering intelligence dashboard. It connects to a user's GitHub account and turns authorized GitHub data into clear visual and actionable insights, primarily for a DevOps engineer who wants to stay connected with software development.

DevPulse is **not** an employee-monitoring platform, a developer-ranking system, a productivity-scoring application, a tool for comparing developers, or a repository source-code storage platform. Requirements must use neutral, evidence-based language. Commit counts, pull-request counts, and technology detections are never proof of productivity, performance, or verified skill.

Approved stack:

- Frontend: React, TypeScript, Vite, React Router, Tailwind CSS, Apache ECharts, Vitest, React Testing Library, Playwright
- Backend: Python, FastAPI, Pydantic, SQLAlchemy 2.x, Alembic, Pytest
- Data: PostgreSQL. Celery and Redis are introduced in a later phase.
- Runtime and delivery: Docker, Docker Compose, GitHub Actions

Approved architecture: **feature-oriented layered modular monolith** (Router -> Service -> Repository or external integration client -> infrastructure). Requirements must not contradict it, but must also not prescribe class names, tables, or endpoints (that is design-stage work).

## 3. Human intent for this phase (authoritative, in the owner's words)

> GitHub must act as both my application authentication and the authorization for GitHub data. Once the user authenticates using GitHub, the application should use the user's GitHub profile data (name, avatar, username, email) in a separate Profile section.
>
> It should work like a tool configuration. The user has to configure their connection with GitHub, and after successful authorization DevPulse must persist the connection metadata and the credentials it legitimately needs in PostgreSQL tables.
>
> The long-term data flow is: Application -> PostgreSQL tables <- GitHub data source. Background jobs (Celery) will later run on an interval to pull the latest updates from GitHub into PostgreSQL, and the application will load all widgets, charts, and visual infographics only from PostgreSQL.

### 3.1 How this intent is scoped into phases

The full intent is delivered across phases. **This run specifies Phase 2 only.**

| Part of the intent | Phase |
|---|---|
| GitHub as authentication, local user, Profile section | Phase 2 (this run) |
| Tool Configuration: connect GitHub, persist connection metadata, connection and permission status, disconnect | Phase 2 (this run) |
| Repository discovery, repository selection, manual sync, sync jobs | Phase 3 (later) |
| Dashboard widgets and charts reading from PostgreSQL | Phases 4-8 (later) |
| Webhooks, Celery, Redis, scheduled synchronization | Phase 9 (later) |

Phase 2 must establish the foundation these later phases rely on (a verified, user-owned GitHub connection), without implementing any of them.

### 3.2 How "persist credentials" must be interpreted (binding)

The phrase "persist credentials in PostgreSQL" must **not** be read as "store raw secrets in ordinary tables". Specify the following instead:

| Item | Required handling |
|---|---|
| DevPulse session credential | Random, high-entropy, opaque. Only a cryptographic hash is persisted. The raw value is never stored in PostgreSQL. |
| GitHub App private key | Never in normal PostgreSQL application tables. Held in a managed secret store in production, or a protected environment-mounted secret locally. Never committed, never returned to React, never logged, never shown in errors. |
| GitHub installation access tokens | Short-lived. Generated only when an approved GitHub operation needs one. Not treated as permanent credentials. Preferably not persisted. |
| GitHub user access and refresh tokens | The design stage decides whether they are needed after authentication and profile retrieval. If not needed, they are not persisted. If needed: application-level encryption, keys stored outside PostgreSQL, scope and expiry metadata, rotation and revocation support, never exposed to React, never logged, never plaintext. |
| Connection metadata (installation ID, account, permissions, status, timestamps) | Persisted in PostgreSQL. |

The specification must state this table's rules as security requirements. Whether user tokens are persisted is an **open decision**, not something you decide.

## 4. Phase 2 scope (in scope)

1. GitHub user authorization used as DevPulse authentication ("Continue with GitHub")
2. Creating or updating the local user, keyed by the **stable GitHub user ID** (never username, display name, or email)
3. Persisting authorized GitHub profile metadata: stable GitHub user ID, username, display name when available, avatar URL, authorized email when available, GitHub profile URL, account type, DevPulse account creation timestamp, last login timestamp, last profile refresh timestamp
4. PostgreSQL-backed opaque DevPulse sessions
5. Session restoration, expiration, and revocation
6. Protected FastAPI APIs (authentication enforced server-side, independent of React route guards)
7. Protected React routes
8. A separate Profile section
9. Profile metadata refresh
10. GitHub App installation
11. All-repositories authorization
12. Selected-repositories authorization
13. Installation verification before an installation is marked active
14. Installation metadata persistence
15. Tool Configuration metadata persistence
16. Connection-status display
17. Permission-status display
18. Logout
19. GitHub disconnection that does **not** log the user out of DevPulse
20. Secure credential-handling requirements (Section 3.2)
21. BDD acceptance behavior

## 5. Phase 2 non-goals (out of scope: must not be specified as work)

- Commits, pull requests, pull-request reviews, issues
- Repository language retrieval, technology detection
- Workflows and workflow-run retrieval
- Repository analytics, dashboard widgets, dashboard charts
- Celery, Redis, Celery Beat, background jobs, scheduled synchronization
- Manual repository-data synchronization, and any synchronization control in the UI
- GitHub webhooks, repository reconciliation
- Repository source-code storage
- GitLab, Bitbucket
- Email-and-password authentication

Where the UI or data model must hint at a later phase, specify a neutral placeholder only (for example, the Profile shows "Not yet synchronized"). Non-goals must appear in `spec.md` as an explicit section, and the acceptance feature must include a scenario proving Phase 2 performs no repository-activity synchronization.

## 6. Decisions already made (do not reopen, do not contradict)

- GitHub is the only MVP identity provider. There is no separate email-and-password system.
- DevPulse still creates its own local user and its own application session.
- Preferred direction: **one GitHub App** providing user authorization (identity) and installation (repository authorization). This remains subject to design-stage confirmation; list it in `open-questions.md` as "preferred, to be confirmed", not as settled.
- GitHub **authentication** and GitHub **repository authorization** are separate states, even when one GitHub App serves both:
  - Authenticated: No / Installed: No / Repository access: No
  - Authenticated: Yes / Installed: No / Repository access: No
  - Authenticated: Yes / Installed: Yes / Repository access: Yes
- Logout revokes the DevPulse session and preserves the GitHub App installation.
- Disconnecting GitHub disables repository access and keeps the user logged in to DevPulse.
- If GitHub provides no email: authentication, user creation, and session creation must still succeed; the Profile shows `Email not available from GitHub`; DevPulse never invents an email.
- A GitHub installation ID is unique. Duplicate callbacks never create duplicate records. An installation is never silently reassigned to another DevPulse user. An installation callback with no valid DevPulse session is never associated with an unknown user.
- The browser never calls GitHub for analytics data. PostgreSQL is the system of record. (Stated as a rule for later phases; nothing in Phase 2 implements it.)
- Session approach (preferred direction): opaque server-side session, PostgreSQL-backed, HTTP-only cookie, Secure in production, approved SameSite policy, expiration, revocation, logout, restoration after browser refresh, session fixation protection. The exact parameters are open decisions.
- Credentials never appear in: `localStorage`, `sessionStorage`, JavaScript-readable cookies, React persistent state, URLs, query parameters, frontend API responses, logs, Celery arguments, user-visible errors, or real test fixtures.

## 7. Connection states to specify

Not configured, Authentication completed, Installation required, Connected, Permission attention required, Suspended, Installation deleted, Verification failed, Disconnected.

For each state, the spec must define: how a user enters it, what the Tool Configuration page shows, what actions are available, and how it exits. Tool Configuration must (eventually) show: provider name, connected GitHub user, installation account and account type, DevPulse authentication status, GitHub installation status, repository-authorization mode, authorized repository count when available, permission status, configuration status, last verification timestamp, and Manage installation, Disconnect, and Reconnect actions. It must show **no** synchronization controls in Phase 2.

Planned persisted installation metadata (requirements-level, not a schema): internal connection ID, owning DevPulse user, GitHub installation ID, installation account ID, account login, account type, repository-selection mode, granted permission metadata, installation status, connection status, installation created timestamp when available, local created and updated timestamps, last verification timestamp, suspension timestamp when applicable, disconnection timestamp when applicable.

## 8. Open decisions (record, never decide)

Put each of these in `open-questions.md` with: question, why it matters, 2-4 options, trade-offs, a recommendation with concise rationale (no hidden chain-of-thought), and what it blocks. Add any further ambiguity you find.

- Default session lifetime, absolute lifetime, idle timeout, fixed versus sliding expiration
- Whether multiple concurrent sessions per user are allowed
- Exact SameSite policy and cookie name
- Session cleanup strategy
- One GitHub App versus separate OAuth App and GitHub App (preferred: one)
- Whether user access and refresh tokens must be persisted after authentication and profile retrieval
- Whether organization installations are in Phase 2 or personal accounts only
- How a reconnect behaves when the installation was deleted or suspended externally
- Behavior when GitHub uninstall (external) fails during disconnection
- Which GitHub permissions the App requests (least privilege; any increase later needs explicit approval)
- Whether disconnection also calls GitHub to uninstall, or only disables locally
- OAuth state lifetime and storage approach
- CSRF protection approach for cookie-authenticated, state-changing requests (logout, disconnect, installation start). This is an addition by the document author, not an earlier decision: record it as an open question and, in `spec.md`, state only the requirement that such requests must be protected against cross-site request forgery.

## 9. Required output: the requirements package (and nothing else)

Create exactly this structure:

```text
specs/
└── phase-02-github-connection/
    ├── spec.md
    ├── assumptions.md
    ├── open-questions.md
    ├── requirements-bdd-coverage.md
    └── features/
        ├── github-authentication.feature.md
        ├── authenticated-session.feature.md
        ├── github-profile.feature.md
        ├── protected-resources.feature.md
        ├── github-app-installation.feature.md
        ├── tool-configuration.feature.md
        ├── github-connection-status.feature.md
        ├── github-disconnection.feature.md
        ├── credential-protection.feature.md
        └── phase-02-acceptance.feature.md
```

### 9.1 `spec.md` must contain

Purpose; Scope; Goals; Non-goals; Actors; User journeys; Functional requirements; Security requirements; Data requirements; UI requirements; Business rules; Error conditions; Assumptions (summary, details in `assumptions.md`); Open decisions (summary, details in `open-questions.md`); Acceptance criteria; Definition of Done.

Requirement rules:

- Every requirement has a unique, stable ID with a category prefix: `FR-` functional, `SR-` security, `DR-` data, `UI-` interface, `BR-` business rule, `ER-` error condition. Example: `FR-AUTH-001`.
- Every requirement is atomic, testable, and uses "must" or "must not".
- Requirements describe **what**, never **how**. No table names, class names, endpoint paths, SQL, or component names.
- Each requirement marks its priority (Must / Should / Could) and the phase source (intent, handoff decision, or your inference). Mark inferences clearly as `[INFERRED]` so the owner can challenge them.
- Use neutral language consistent with Section 2.

### 9.2 Feature files (Gherkin in Markdown)

Format rules:

- Every feature file is a Markdown file named `<name>.feature.md` (never a bare `.feature`). If a bare `.feature` file of the same name exists, replace it; do not leave duplicates.
- Each file contains a one-line `#` heading with the feature name, then **one** fenced code block marked `gherkin` that holds the complete Gherkin text (Feature, Background, tags, Scenarios, Scenario Outlines, Examples). Nothing inside the fence is Markdown-formatted; the fenced text must be valid Gherkin so it can later be extracted unchanged.
- Any notes for the reviewer go outside the fence, below it, under a `## Reviewer notes` heading.

Content rules:

- Describe observable behavior only. **Do not** mention Python classes, SQL, React components, internal method names, or implementation details.
- Each scenario is tagged with the requirement IDs it covers (for example `@FR-AUTH-001`) and with `@critical` and/or `@security` where applicable.
- Cover success paths, failure paths, boundary cases, ownership cases, security cases, and idempotency cases.
- Use `Background` and `Scenario Outline` to avoid duplication, but keep each scenario independently understandable.
- Use consistent, business-readable actors and terms.

Minimum behavior to cover (add more if you find gaps):

**github-authentication.feature.md**: start authorization; new-user authentication; existing-user authentication; changed profile data updates the existing user (no duplicate); missing email; user cancels; GitHub denies; missing code; missing state; invalid state; expired state; reused state; mismatched state; temporary GitHub failure.

**authenticated-session.feature.md**: secure session creation; session restoration after refresh; current-user retrieval; missing, invalid, expired, and revoked session; logout; idempotent logout; session fixation prevention; cookie-security expectations.

**github-profile.feature.md**: display metadata; missing-email state; refresh profile; update changed metadata; stable identity preserved when username changes; refresh authorization failure; temporary refresh failure; no credential exposure; cross-user denial.

**protected-resources.feature.md**: authenticated and unauthenticated API access; authenticated and unauthenticated route access; missing, expired, and revoked sessions; cross-user access; safe login redirection (no open redirect).

**github-app-installation.feature.md**: start installation; personal installation; organization installation if approved; all repositories; selected repositories; cancellation; successful callback; no authenticated session; missing installation ID; invalid callback correlation; duplicate callback; ownership conflict; verification failure.

**tool-configuration.feature.md**: before installation; after installation; provider and account details; repository-authorization mode; permission status; manage installation; reconnection; no Phase 2 synchronization controls; user isolation.

**github-connection-status.feature.md**: not configured; installation required; connected; suspended; permission attention required; installation deleted; verification failed; disconnected; user isolation.

**github-disconnection.feature.md**: request disconnection; confirmation; cancellation; successful disconnection; DevPulse session preserved; future repository access prevented; repeated disconnection; external uninstall failure; already-removed installation; cross-user denial.

**credential-protection.feature.md**: no tokens in responses; no tokens in browser storage; raw session credential not persisted; private key outside normal database tables; no secrets in logs, errors, or URLs; required stored tokens encrypted; callback replay protection.

**phase-02-acceptance.feature.md**: new-user login-and-installation journey; returning user with installation; authenticated user without installation; missing-email journey; logout preserves installation; disconnection preserves DevPulse session; suspended installation; deleted installation; proof that Phase 2 does not synchronize repository activity.

### 9.3 `requirements-bdd-coverage.md`

A traceability matrix with these columns: Requirement ID | Priority | Summary | Feature file | Scenario name(s) | Coverage status (Covered / Partial / Gap).

- Every requirement must map to at least one scenario.
- Every scenario must map to at least one requirement.
- Any Partial or Gap row must explain why and point to the matching open question.
- End with a coverage summary: counts per category, and an explicit list of gaps.

### 9.4 `assumptions.md`

Each assumption: ID, statement, source (handoff / inference / repository observation), risk if wrong, how to validate. Never present an assumption as a decision.

### 9.5 `open-questions.md`

As described in Section 8. Number them (`OQ-001`...), and state which requirements or scenarios each one blocks.

## 10. Self-check before you stop

Verify, and report the result in your final message:

1. Only the files in Section 9 were created or changed.
2. No non-goal (Section 5) appears as in-scope work.
3. No implementation detail leaked into requirements or Gherkin.
4. Every requirement and every scenario is traceable both ways.
5. Every decision in Section 8 is in `open-questions.md`, not decided.
6. The credential-handling rules in Section 3.2 appear as security requirements.
7. Inferences are marked `[INFERRED]`.

## 11. Stop condition

After the self-check, **stop**. Do not begin design, planning, tests, or code. End your final message with:

```text
STATE: AWAITING_REQUIREMENTS_APPROVAL
```

and list the available commands:

```text
REVISE_PHASE_2_REQUIREMENTS          (with the changes requested)
APPROVE_PHASE_2_REQUIREMENTS         (only the human may send this)
```

Do not interpret silence, praise, or partial feedback as approval. Only the exact command `APPROVE_PHASE_2_REQUIREMENTS` moves the workflow forward.