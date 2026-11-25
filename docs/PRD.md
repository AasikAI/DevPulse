# DevPulse Product Requirements Document

| Field | Value |
|---|---|
| Product | DevPulse |
| Document type | Product Requirements Document (PRD) |
| Version | 1.0 |
| Status | Draft for review |
| Product owner | Ahamed |
| Primary platform | Responsive web application |
| Initial integration | GitHub.com |
| Last updated | 2026-11-21 |

---

## 1. Executive summary

DevPulse is a personal engineering intelligence dashboard that connects to a user's GitHub account and converts development activity into clear, visual, and actionable insights.

The product is intended primarily for DevOps engineers who want to remain connected with application development while continuing to work across CI/CD, containers, infrastructure, and operations. It helps the user understand what they have worked on, which technologies they are currently exposed to, how pull requests are progressing, and how reliably GitHub Actions workflows are running.

DevPulse is not an employee-monitoring, developer-ranking, or productivity-scoring system. It presents evidence-based activity and engineering-health indicators without judging developer performance.

## 2. Problem statement

DevOps engineers frequently work across deployment pipelines, infrastructure, observability, containers, and operational support. Over time, this can reduce their visibility into day-to-day application-development practices and emerging tools used inside repositories.

GitHub already contains useful signals such as commits, pull requests, reviews, dependency manifests, repository languages, and workflow executions. However, these signals are distributed across repositories and GitHub pages. A user must manually inspect multiple locations to understand:

- Recent development activity
- Technologies and frameworks currently in use
- Pull requests requiring attention
- Review participation
- CI/CD success and failure patterns
- Repeated workflow failures
- Changes in technology exposure over time

DevPulse will consolidate these signals into one personal, visual dashboard.

## 3. Product vision

> Help DevOps engineers stay connected with software development by turning GitHub activity, technology usage, pull-request data, and CI/CD execution history into understandable visual insights.

## 4. Product principles

1. **Evidence over scoring**  
   Show measurable activity and trends without producing a developer-performance score.

2. **Explain every insight**  
   Every generated insight must include the underlying metric, time period, and relevant repository.

3. **Secure by default**  
   Request only required GitHub permissions, keep credentials server-side, and avoid storing source code unless a future approved requirement makes it necessary.

4. **Progressive complexity**  
   Begin with manual synchronization and deterministic analytics. Introduce webhooks, background workers, and advanced insights only after the foundational flow is reliable.

5. **Personal engineering awareness**  
   Optimize the first release for an individual user rather than team surveillance or organizational reporting.

6. **Actionable visualizations**  
   Charts must help the user identify a trend, risk, or next action rather than exist only for decoration.

## 5. Goals

### 5.1 Primary goals

- Allow a user to securely connect a GitHub account.
- Import activity from repositories authorized by the user.
- Visualize commits, pull requests, reviews, issues, and repository activity.
- Detect languages, frameworks, libraries, databases, testing tools, and DevOps tools used in repositories.
- Visualize GitHub Actions workflow reliability, failures, and duration trends.
- Generate neutral, rule-based observations supported by measurable data.
- Provide repository and date-based filtering throughout the dashboard.
- Build the product using a modern development stack that strengthens the owner's hands-on skills in React, Python, FastAPI, PostgreSQL, Docker, testing, CI/CD, and observability.

### 5.2 Secondary goals

- Demonstrate secure GitHub integration as a portfolio project.
- Provide a foundation for future GitLab, Bitbucket, or Jira integrations.
- Support future team-level analytics without designing the MVP as an employee-monitoring tool.
- Allow future export of personal engineering metrics.

## 6. Non-goals for the initial product

The initial release will not:

- Rank developers or compare employee productivity.
- Produce a single productivity, performance, or skill score.
- Modify repositories, pull requests, issues, or workflows.
- Store full repository source code, patches, or private comments.
- Perform AI-based code review.
- Predict individual performance or delivery dates.
- Support GitLab or Bitbucket.
- Support GitHub Enterprise Server.
- Integrate with Jira.
- Deploy through Kubernetes as an initial requirement.
- Use microservices.
- Provide billing, subscriptions, or multi-tenant enterprise administration.

## 7. Target users

### 7.1 Primary persona: DevOps engineer maintaining development awareness

**Profile**

- Works with CI/CD, containers, deployment automation, and production support.
- Has application-development experience or wants to strengthen it.
- Uses GitHub across personal or approved work repositories.
- Wants a concise view of application and pipeline activity.

**Technology interests**

- JavaScript and TypeScript
- React
- Python
- FastAPI
- PostgreSQL
- Docker and Docker Compose
- GitHub Actions
- Testing tools such as Pytest, Vitest, Jest, React Testing Library, and Playwright

**Main needs**

- Understand recent development participation.
- See technologies currently used across active repositories.
- Identify pull requests and reviews requiring attention.
- Detect unstable GitHub Actions workflows.
- Recognize learning gaps and newly encountered technologies.

### 7.2 Future personas

- Full-stack developer tracking personal engineering activity
- Technical lead reviewing repository health without ranking people
- Engineering manager reviewing team-level delivery signals
- Platform engineer monitoring workflow reliability across repositories

Future personas require separate privacy, consent, access-control, and metric-governance requirements.

## 8. Value proposition

DevPulse provides one place to answer:

- What did I work on recently?
- Which repositories were active?
- Which languages, frameworks, and tools did I encounter?
- Which pull requests are open, old, blocked, or waiting for review?
- How reliable are my GitHub Actions workflows?
- Which workflows repeatedly fail or take longer than usual?
- Which technologies are new or becoming less visible in my recent work?

## 9. Product scope

### 9.1 MVP scope

The MVP will support:

- One user and one connected GitHub identity
- GitHub.com
- GitHub OAuth authentication
- GitHub App installation for repository authorization
- Selection of one or more repositories
- Manual synchronization
- Activity data for configurable 7-day, 30-day, and 90-day periods
- Overview dashboard
- Development activity analytics
- Technology detection
- Pull-request analytics
- GitHub Actions analytics
- Basic repository details
- Rule-based personal insights
- Dark and light themes
- Responsive desktop and mobile layouts

### 9.2 Post-MVP scope

Potential later capabilities include:

- GitHub webhooks and incremental synchronization
- Scheduled reconciliation jobs
- Multiple GitHub installations
- Organization account support at larger scale
- Notification preferences
- User-configurable insight thresholds
- Export to CSV or PDF
- Team dashboards with explicit consent and access controls
- GitLab and Bitbucket providers
- Jira correlation
- LLM-assisted explanations grounded in stored metrics

## 10. Core user journey

1. The user opens DevPulse.
2. The user selects **Continue with GitHub**.
3. GitHub authenticates the user.
4. DevPulse creates or updates the user and starts a secure session.
5. The user installs the DevPulse GitHub App.
6. The user grants access to all repositories or selected repositories.
7. DevPulse retrieves the repositories available to the installation.
8. The user selects the repositories to track.
9. DevPulse starts an initial synchronization.
10. The user sees synchronization progress and any partial failures.
11. DevPulse displays the overview dashboard.
12. The user filters metrics by repository and date range.
13. The user opens technology, pull-request, CI/CD, repository, or insight views.
14. The user can manually synchronize, disconnect GitHub, or delete imported data.

## 11. Functional requirements

Requirements use the format `FR-<module>-<number>`.

### 11.1 Authentication and account

#### FR-AUTH-001: GitHub sign-in

DevPulse must allow an unauthenticated user to start GitHub authentication.

#### FR-AUTH-002: User creation and update

After successful authentication, DevPulse must create a new user or update the existing user identified by the stable GitHub user ID.

A changed GitHub username must not create a duplicate DevPulse user.

#### FR-AUTH-003: Secure application session

DevPulse must create a server-controlled session and provide the browser with an HTTP-only session cookie.

#### FR-AUTH-004: Session restoration

DevPulse must recognize a valid session after browser refresh without requiring the user to authenticate again.

#### FR-AUTH-005: Protected resources

Protected frontend pages and backend endpoints must reject unauthenticated access.

#### FR-AUTH-006: Logout

The user must be able to revoke the current DevPulse session. Logging out must not uninstall the GitHub App.

### 11.2 GitHub connection

#### FR-GH-001: GitHub App installation

An authenticated user must be able to start and complete installation of the DevPulse GitHub App.

#### FR-GH-002: Repository authorization choices

The GitHub installation must support access to all repositories or repositories selected by the user.

#### FR-GH-003: Installation association

DevPulse must associate a verified GitHub installation with the authenticated DevPulse user.

#### FR-GH-004: Installation uniqueness

A GitHub installation ID must be unique and must not be silently reassigned to a different DevPulse user.

#### FR-GH-005: Connection status

DevPulse must represent at least these states:

- Not connected
- Connected
- Suspended
- Permission attention required
- Disconnected
- Verification failed

#### FR-GH-006: Disconnect GitHub

The user must be able to disconnect GitHub without ending the DevPulse login session.

#### FR-GH-007: Minimum permissions

The GitHub App must request only the read permissions necessary for approved features.

### 11.3 Repository management

#### FR-REPO-001: Retrieve available repositories

DevPulse must retrieve repositories available to the active GitHub installation.

#### FR-REPO-002: Repository selection

The user must be able to select all available repositories or individual repositories for tracking.

#### FR-REPO-003: Repository filtering

The selection interface must support search and filters for visibility and primary language.

#### FR-REPO-004: Repository metadata

For each tracked repository, DevPulse must store the GitHub repository ID, owner, name, full name, description, visibility, default branch, primary language, archived status, relevant GitHub timestamps, and last synchronization time.

#### FR-REPO-005: Idempotent import

Repeated synchronization of the same GitHub repository must update the existing record and must not create a duplicate.

#### FR-REPO-006: Repository details

The user must be able to open a repository view containing its activity, technologies, pull requests, and workflow information.

### 11.4 Synchronization

#### FR-SYNC-001: Manual synchronization

The user must be able to initiate synchronization for all selected repositories or an individual selected repository.

#### FR-SYNC-002: Synchronization status

A synchronization job must report one of the following states:

- Pending
- Running
- Completed
- Partially completed
- Failed
- Cancelled

#### FR-SYNC-003: Progress visibility

The UI must display the current state, repositories processed, failures, and completion time for an initial synchronization.

#### FR-SYNC-004: Idempotent processing

Reprocessing the same GitHub object must not create duplicate records.

#### FR-SYNC-005: Partial failure

Failure to synchronize one repository or data category must not discard successfully processed data from other repositories or categories.

#### FR-SYNC-006: Rate-limit handling

DevPulse must detect GitHub rate-limit conditions, avoid uncontrolled retry loops, and tell the user when synchronization can be retried.

#### FR-SYNC-007: Future incremental updates

The design must allow later addition of GitHub webhooks and scheduled reconciliation without replacing the core domain model.

### 11.5 Overview dashboard

#### FR-DASH-001: Summary metrics

The overview must display:

- Commit count
- Pull requests opened
- Pull requests merged
- Reviews completed
- Active repositories
- GitHub Actions success rate

#### FR-DASH-002: Global filters

The overview must support repository and date-range filters. Initial date ranges are 7, 30, and 90 days.

#### FR-DASH-003: Filter consistency

Changing a global filter must update all visible metrics and charts using the same scope.

#### FR-DASH-004: Development trend

The overview must visualize development activity over time, including commits, pull requests, and reviews.

#### FR-DASH-005: Contribution heatmap

The overview must provide a date-based activity heatmap with accessible tooltips or equivalent details.

#### FR-DASH-006: Repository activity

The overview must visualize activity grouped by repository.

#### FR-DASH-007: Pull-request distribution

The overview must visualize pull requests by meaningful states such as open, merged, closed, and draft.

#### FR-DASH-008: Recent activity

The overview must show a chronological feed of relevant recent events.

#### FR-DASH-009: Metric interpretation

The UI must not present commit count or another isolated activity measure as a productivity or performance score.

### 11.6 Development activity analytics

#### FR-ACT-001: Supported activity

DevPulse must support analytics for commits, pull requests, pull-request reviews, issues, and selected repository events.

#### FR-ACT-002: Activity dimensions

The user must be able to view activity by date, repository, event type, and day of week.

#### FR-ACT-003: Active development days

DevPulse must calculate the number of days containing at least one supported development event within the selected period.

#### FR-ACT-004: Pagination

Long activity feeds must use pagination or bounded incremental loading.

#### FR-ACT-005: Neutral presentation

Activity analytics must use neutral labels such as *recent activity*, *development trend*, and *repository activity*.

### 11.7 Technology detection and exposure

#### FR-TECH-001: Language detection

DevPulse must record repository language distribution using GitHub language data.

#### FR-TECH-002: Manifest inspection

DevPulse must detect approved technologies from known manifests and configuration files, including:

- `package.json`
- `requirements.txt`
- `pyproject.toml`
- `Dockerfile`
- `compose.yml` and `docker-compose.yml`
- `.github/workflows/*.yml`
- `pytest.ini`
- `vite.config.*`
- `tsconfig.json`
- `alembic.ini`
- Terraform files
- Helm `Chart.yaml`
- Kubernetes resource manifests

#### FR-TECH-003: Initial technology catalogue

The initial detection catalogue must support at least:

- JavaScript
- TypeScript
- React
- Vite
- Next.js
- Python
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL clients
- Pytest
- Jest
- Vitest
- Docker
- Docker Compose
- GitHub Actions
- Terraform
- Helm
- Kubernetes
- Redis
- Celery

#### FR-TECH-004: Detection evidence

Every detected technology must include the repository, detection method, source filename, first detected date, and last detected date.

#### FR-TECH-005: Source minimization

The product must not persist complete source or manifest content solely for technology detection.

#### FR-TECH-006: Technology views

The user must be able to view:

- Technology badges by category
- Language distribution
- Technology activity over time
- Repository-to-technology mapping
- Newly detected technologies
- Detection evidence

#### FR-TECH-007: Exposure terminology

Technology metrics must be described as repository exposure or recent activity, not as a verified skill level.

### 11.8 Pull-request insights

#### FR-PR-001: Pull-request states

DevPulse must represent open, merged, closed, and draft pull requests.

#### FR-PR-002: Pull-request metrics

DevPulse must calculate:

- Open pull requests
- Merged pull requests
- Draft pull requests
- Pull requests waiting for review
- Average time to merge
- Median time to merge
- Pull-request age
- Review participation
- Pull-request size using additions and deletions

#### FR-PR-003: Pull-request filters

The pull-request view must support filters for repository, status, author, CI status, and date range.

#### FR-PR-004: Pull-request list

The list must show title, repository, number, author, status, size, review state, CI state, age, and last update.

#### FR-PR-005: Attention indicators

The product should help identify old open pull requests, pull requests waiting for review, and pull requests with failed CI without assigning blame.

### 11.9 GitHub Actions and CI/CD insights

#### FR-CI-001: Workflow-run import

DevPulse must import workflow name, repository, branch, commit SHA, trigger, actor, status, conclusion, start time, completion time, and duration.

#### FR-CI-002: Status and conclusion

Workflow execution status and conclusion must be stored separately.

Supported statuses include queued, in progress, and completed.

Supported conclusions include success, failure, cancelled, skipped, timed out, and action required.

#### FR-CI-003: Success-rate calculation

CI success rate must be calculated as successful completed runs divided by all completed runs. Queued and running workflows must not be included in the denominator.

#### FR-CI-004: CI/CD metrics

DevPulse must provide:

- Success rate
- Successful-run count
- Failed-run count
- Cancelled-run count
- Average duration
- P95 duration when sufficient data exists
- Failure rate by workflow
- Failure rate by repository
- Recent failures
- Repeated failures

#### FR-CI-005: Workflow views

The user must be able to filter workflow runs by repository, workflow, branch, status, conclusion, and date range.

#### FR-CI-006: Needs-attention rules

The initial product must support configurable deterministic rules such as:

- Repeated failure: the same workflow fails at least three times in seven days.
- Duration regression: average duration increases by more than 25 percent with at least five comparable runs.
- Stale failure: no successful run follows a failure for more than 24 hours.
- Low reliability: success rate falls below 80 percent with at least ten completed runs.

#### FR-CI-007: Failure details

Every CI/CD alert must identify the workflow, repository, branch when available, supporting metric, time period, and a link or action to inspect the workflow.

### 11.10 Personal insights

#### FR-INS-001: Deterministic insights

The first version must generate insights using approved rules rather than an LLM.

#### FR-INS-002: Insight evidence

Every insight must contain:

- Category
- Title
- Explanation
- Supporting metric
- Time period
- Related repositories
- Severity
- Suggested action
- Generated timestamp

#### FR-INS-003: Insight severity

Initial severity values are:

- Information
- Positive
- Attention

#### FR-INS-004: Insight actions

The user must be able to save or dismiss an insight.

#### FR-INS-005: Neutral language

Insights must not rank, shame, or make unsupported claims about productivity or skill.

### 11.11 Settings, privacy, and data control

#### FR-SET-001: Account settings

The user must be able to view the connected GitHub username, installation state, and repository permission mode.

#### FR-SET-002: Appearance

The user must be able to choose light, dark, or system theme.

#### FR-SET-003: Synchronization controls

The user must be able to view the last successful synchronization and synchronization history and initiate an allowed manual synchronization.

#### FR-SET-004: Imported-data deletion

The user must be able to delete imported GitHub activity and analytics data.

#### FR-SET-005: Account deletion

The user must be able to request deletion of the DevPulse account and associated stored data.

#### FR-SET-006: Data export

Data export is a post-MVP requirement unless specifically promoted into the MVP scope.

## 12. User experience requirements

### UX-001: Responsive interface

The application must be usable at desktop, tablet, and mobile widths, with 1440 px, 768 px, and 390 px used as primary design references.

### UX-002: Primary navigation

The primary navigation must include:

- Overview
- Development Activity
- Technologies
- Pull Requests
- CI/CD
- Repositories
- Insights
- Settings

### UX-003: Required interface states

Every data-driven page must define appropriate states for:

- Loading
- Empty data
- Initial synchronization
- Partial synchronization
- Completed synchronization
- Rate limit reached
- Permission removed
- Recoverable error
- Unrecoverable error
- Backend unavailable

### UX-004: Accessibility

- Text and controls must target WCAG 2.2 AA contrast and interaction requirements.
- Interactive controls must be keyboard accessible.
- Charts must provide text labels, tooltips, summaries, tables, or equivalent accessible descriptions.
- Status must not be communicated through colour alone.
- Focus indicators must remain visible.

### UX-005: Technical visual language

Repository names, branches, commit SHAs, workflow names, and technical identifiers should use a monospace type style where practical.

### UX-006: Consistent filters

Repository and date filters must behave consistently across overview, activity, technology, pull-request, and CI/CD views.

## 13. Data model overview

The initial domain model is expected to include:

- Users
- User sessions
- GitHub accounts
- GitHub installations
- Repositories
- Repository selections
- Synchronization jobs
- Synchronization job items
- Commits
- Pull requests
- Pull-request reviews
- Issues
- Activity events
- Repository languages
- Technologies
- Technology detection rules
- Repository technology detections
- Workflows
- Workflow runs
- Daily metrics
- Personal insights
- Insight user actions
- Webhook deliveries in a later phase

Stable GitHub object IDs must be used for uniqueness wherever GitHub provides them.

## 14. Non-functional requirements

### 14.1 Security

#### NFR-SEC-001: Credential handling

GitHub access tokens, installation tokens, client secrets, private keys, webhook secrets, authorization headers, and session credentials must not appear in frontend responses or application logs.

#### NFR-SEC-002: Session protection

Production cookies must be HTTP-only, Secure, time-limited, and configured with an appropriate SameSite policy.

#### NFR-SEC-003: Callback protection

Authentication and installation callbacks must validate short-lived, single-use state or equivalent request correlation.

#### NFR-SEC-004: Webhook validation

When webhooks are introduced, every delivery must be signature-validated and idempotently processed using the GitHub delivery ID.

#### NFR-SEC-005: Authorization boundaries

Every user-scoped resource query and mutation must enforce ownership on the server.

#### NFR-SEC-006: Secret management

Production secrets must be provided through a managed secret store or protected deployment environment, not committed to the repository.

#### NFR-SEC-007: Dependency and image scanning

The CI pipeline should scan Python and JavaScript dependencies and container images before production deployment.

### 14.2 Performance

#### NFR-PERF-001: API latency

For cached or database-backed dashboard reads, the target p95 API response time is under 750 ms under expected single-user or small-user MVP load, excluding initial GitHub synchronization.

#### NFR-PERF-002: Initial page usability

The application shell should become usable within approximately 3 seconds on a typical broadband connection, with charts allowed to load progressively.

#### NFR-PERF-003: Background work

Long-running GitHub synchronization and technology-detection operations must not block request threads once background processing is introduced.

#### NFR-PERF-004: Bounded queries

Activity and workflow lists must use pagination and bounded date ranges. Unbounded repository-history retrieval is not allowed.

### 14.3 Reliability

#### NFR-REL-001: Idempotency

Repository imports, GitHub object imports, installation callbacks, and future webhook deliveries must be safely repeatable.

#### NFR-REL-002: Retry policy

External API retries must use bounded exponential backoff with jitter and must stop for authentication, permission, and non-retryable validation failures.

#### NFR-REL-003: Partial success

A partial GitHub failure must preserve completed work and expose failed items for retry.

#### NFR-REL-004: Data backup

A production deployment must include scheduled PostgreSQL backups and a documented restore procedure.

### 14.4 Observability

#### NFR-OBS-001: Structured logs

Backend and worker logs must be structured and include relevant correlation fields such as request ID, sync job ID, repository ID, and webhook delivery ID.

#### NFR-OBS-002: Metrics

The product should expose metrics for:

- API request duration and errors
- GitHub API calls and failures
- Synchronization duration and failures
- Database connection usage
- Background task duration and failures
- Webhook processing latency when introduced

#### NFR-OBS-003: Health checks

The backend must expose liveness and readiness endpoints. Readiness must verify required dependencies such as PostgreSQL and, when introduced, Redis.

#### NFR-OBS-004: Tracing

OpenTelemetry-compatible tracing should be introduced for API, GitHub client, database, and background-task boundaries before production-scale rollout.

### 14.5 Maintainability

#### NFR-MNT-001: Architecture

The product must begin as a modular monolith. Microservices require a separately approved need.

#### NFR-MNT-002: Database migrations

All database schema changes must use Alembic migrations and must be validated in CI.

#### NFR-MNT-003: API contracts

FastAPI request and response schemas must be explicit, versioned under `/api/v1`, and reflected in automated tests.

#### NFR-MNT-004: Traceability

Each implemented requirement must be traceable to BDD scenarios, planned tests, and implementation modules.

## 15. Technical baseline and constraints

| Area | Initial choice |
|---|---|
| Frontend | React with TypeScript and Vite |
| Routing | React Router |
| UI styling | Tailwind CSS with reusable accessible components |
| Charts | Apache ECharts |
| Backend | Python with FastAPI |
| Validation | Pydantic |
| ORM | SQLAlchemy 2.x |
| Database | PostgreSQL |
| Migrations | Alembic |
| Background processing | Celery and Redis, introduced when required |
| Backend testing | Pytest |
| Frontend testing | Vitest and React Testing Library |
| End-to-end testing | Playwright |
| Local runtime | Docker Compose |
| CI/CD | GitHub Actions |
| Observability | Structured logging and OpenTelemetry-compatible instrumentation |

These are approved constraints for planning unless a documented architecture decision proposes and receives approval for a change.

## 16. High-level architecture

```text
React web application
        |
        | HTTPS / JSON
        v
FastAPI modular monolith
        |
        +---- PostgreSQL
        |
        +---- GitHub APIs
        |
        +---- Redis and background worker (later phase)
        |
        +---- Metrics, logs, and traces
```

The dashboard must read normalized and aggregated data from PostgreSQL. It must not retrieve all GitHub data directly on every page load.

## 17. Delivery phases

### Phase 0: Product and technical definition

- PRD
- Figma design
- Architecture constraints
- Initial backlog
- BDD and specification workflow

### Phase 1: Application foundation

- React and FastAPI application shells
- PostgreSQL and Alembic
- Docker Compose
- Health endpoints
- CI pipeline
- Base layout, routing, and error handling

### Phase 2: GitHub authentication and connection

- GitHub sign-in
- Secure application session
- Protected routes and APIs
- GitHub App installation
- Connection status
- Logout and GitHub disconnection

### Phase 3: Repository synchronization

- Available repositories
- Repository selection
- Metadata import
- Sync jobs and status
- Idempotent updates

### Phase 4: Overview dashboard

- Summary cards
- Global filters
- Activity trend
- Contribution heatmap
- Repository and pull-request visualizations

### Phase 5: Development activity analytics

- Commits
- Pull requests
- Reviews
- Issues
- Activity feeds and aggregations

### Phase 6: Technology detection

- GitHub language data
- Manifest inspection
- Detection rules and evidence
- Technology views

### Phase 7: Pull-request insights

- Pull-request metrics
- Merge-time analytics
- Review and CI state
- Attention filters

### Phase 8: GitHub Actions insights

- Workflow runs
- Reliability and duration metrics
- Failure analysis
- Needs-attention rules

### Phase 9: Webhooks and background processing

- Webhook verification
- Incremental updates
- Celery and Redis
- Scheduled reconciliation

### Phase 10: Personal insights

- Deterministic rules
- Evidence-backed observations
- Save and dismiss actions

### Phase 11: Security, testing, and observability

- Security hardening
- Automated test coverage
- Metrics, tracing, and dashboards
- Data deletion validation

### Phase 12: Deployment and release

- Production environment
- HTTPS
- Backups
- Deployment automation
- Smoke tests
- Operational documentation

## 18. Product success metrics

MVP success should be measured using product reliability and user usefulness rather than engagement alone.

### 18.1 Activation

- User successfully authenticates.
- User connects a GitHub installation.
- User selects at least one repository.
- Initial synchronization completes or partially completes with a clear recovery path.
- User reaches the overview dashboard.

Target for controlled testing: at least 90 percent of test users complete the full activation flow without developer intervention.

### 18.2 Data quality

- At least 95 percent of imported GitHub objects are free of duplicate records during repeated synchronization tests.
- Technology detections provide evidence for 100 percent of displayed technologies.
- CI success-rate calculations match a verified fixture dataset for 100 percent of automated calculation tests.
- All displayed insights identify their metric and period.

### 18.3 Reliability

- Zero known credential exposure in responses, browser-readable storage, or logs.
- All critical BDD scenarios pass before phase release.
- No unresolved critical or high-severity security findings at release.
- Manual synchronization failures provide a visible status and retry path.

### 18.4 Usefulness

During user review, the user should be able to identify within two minutes:

- The most active repository in the selected period
- The primary technologies detected
- At least one open or blocked pull request when such data exists
- The least reliable GitHub Actions workflow when sufficient workflow data exists

## 19. Testing and quality strategy

DevPulse will use specification-driven development, behaviour-driven development, and test-driven implementation.

### 19.1 Planning inputs

Each implementation phase will begin with:

1. A phase-specific `spec.md`
2. Gherkin feature files describing observable behaviour

### 19.2 Planning output

Before implementation, the agent must produce:

- Requirement and BDD coverage review
- Architecture decision report with options and trade-offs
- Technical design
- TDD plan
- Vertical-slice implementation plan
- Requirement-to-test traceability matrix
- Risks and assumptions

The agent must stop at an explicit human approval gate before changing production code.

### 19.3 Implementation loop

For each approved vertical slice:

```text
Write failing test
→ Confirm expected failure
→ Add minimum implementation
→ Run relevant tests
→ Refactor without changing behaviour
→ Run regression tests
→ Update traceability
```

### 19.4 Test levels

- Domain unit tests
- Service unit tests
- Repository integration tests using PostgreSQL
- API integration tests
- GitHub client contract tests using recorded or mocked fixtures
- Frontend component tests
- Security tests
- Playwright end-to-end acceptance tests

## 20. Privacy and ethical requirements

- Users must know which GitHub account and repositories are connected.
- Private repository visibility must not be exposed to another user.
- Source code must not be retained solely for analytics.
- Metrics must not be presented as proof of productivity or skill.
- Team features must require explicit access control, purpose definition, and consent review before implementation.
- The user must be able to disconnect GitHub and delete imported data.
- Insight wording must remain factual, neutral, and supported by displayed evidence.

## 21. Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| GitHub API rate limits | Delayed or failed synchronization | Local persistence, bounded pagination, conditional requests where suitable, backoff, and visible retry timing |
| Excessive GitHub permissions | Security and trust risk | Read-only minimum permissions and explicit permission explanation |
| Duplicate data | Incorrect charts and metrics | Stable GitHub IDs, unique constraints, upsert behaviour, and idempotency tests |
| Misleading activity metrics | Users may interpret activity as performance | Neutral labels, no composite score, contextual explanations, and metric definitions |
| Technology false positives | Incorrect exposure insights | Evidence storage, deterministic rules, detection confidence, and rule-specific tests |
| Large repository histories | Slow initial synchronization | Bounded initial lookback, incremental updates, pagination, and background jobs |
| GitHub service outage | Broken authentication or synchronization | Safe errors, retries for transient failures, partial completion, and reconciliation |
| Secret leakage | Repository compromise | Server-side tokens, redaction tests, secure cookies, secret scanning, and least privilege |
| Scope expansion | Delayed MVP | Phase boundaries, explicit non-goals, and human approval gates |
| Dashboard visual overload | Low usability | Limited MVP charts, progressive detail, consistent filters, and accessible summaries |

## 22. Assumptions

- GitHub.com is the only source-control provider in the MVP.
- The initial product is primarily a personal dashboard.
- Users have authority to connect the repositories they select.
- The product can access the GitHub APIs needed for authorized data.
- The initial synchronization will use a bounded lookback period rather than complete repository history.
- PostgreSQL will be the system of record for normalized analytics data.
- Advanced AI explanations are deferred until deterministic metrics and rules are reliable.

## 23. Open decisions

The following decisions must be resolved through phase-specific design review:

1. Whether GitHub identity authentication uses a separate OAuth App or GitHub App user authorization.
2. Session storage strategy and session lifetime.
3. Whether one user can connect multiple installations in the MVP.
4. Initial synchronization lookback limit and object caps.
5. Exact GitHub App permissions required for checks and workflow data.
6. Whether issue analytics remain in the MVP or move to a later release.
7. Retention period for raw activity and workflow-run data.
8. Hosting approach for the first public deployment.
9. Whether Celery is required at Phase 3 or can wait until Phase 9.
10. Thresholds and minimum sample sizes for insight rules.

## 24. MVP release criteria

The MVP is ready for release when:

- Authentication, GitHub connection, repository selection, and synchronization flows work end to end.
- The overview, activity, technology, pull-request, CI/CD, repository, insight, and settings views meet approved acceptance criteria.
- All critical BDD scenarios pass.
- Security tests confirm that credentials are absent from logs, responses, and browser-readable storage.
- Repeated synchronization does not create duplicate GitHub objects.
- Technology detections show evidence.
- Workflow calculations pass verified fixtures.
- Loading, empty, partial-failure, permission, rate-limit, and unavailable states are implemented.
- Production database backup and restore procedures are documented and tested.
- The deployment passes health checks and smoke tests.
- No critical or high-severity defects remain open.
- The product owner gives explicit release approval.

## 25. Definition of done for a phase

A phase is complete only when:

- Approved requirements are implemented.
- Requirement-to-BDD-to-test-to-code traceability is updated.
- Associated automated tests pass.
- Existing regression tests pass.
- Security requirements for the phase are verified.
- Database migrations apply successfully and, where feasible, roll back safely.
- User-visible loading, success, empty, and error states are covered.
- Documentation is updated.
- No implementation deviates from the approved design without recorded approval.
- The product owner approves the phase result.

---

## Appendix A: Initial dashboard metric definitions

| Metric | Initial definition |
|---|---|
| Active repository | A selected repository with at least one supported activity event in the selected period |
| Active development day | A calendar day with at least one supported development event |
| Pull-request merge time | `merged_at - created_at` for merged pull requests |
| CI success rate | Successful completed runs divided by all completed runs, multiplied by 100 |
| Workflow duration | `completed_at - started_at` for completed runs with valid timestamps |
| Technology exposure | Detection of a technology in an authorized repository, not a verified measure of skill |
| Repeated workflow failure | At least three failures for the same workflow in seven days, configurable later |
| Duration regression | More than 25 percent increase in comparable average duration with at least five runs |

## Appendix B: Initial API capability groups

The exact contracts will be defined in phase specifications and approved design documents.

```text
/api/v1/auth/*
/api/v1/github/*
/api/v1/repositories/*
/api/v1/sync/*
/api/v1/dashboard/*
/api/v1/activity/*
/api/v1/technologies/*
/api/v1/pull-requests/*
/api/v1/workflows/*
/api/v1/insights/*
/api/v1/settings/*
/api/v1/health/*
```

## Appendix C: Approval state

Current document state: **DRAFT_FOR_REVIEW**

The next recommended artifact is a phase-specific specification for **Phase 2: GitHub Authentication and Connection**, followed by Gherkin BDD feature files derived from that specification and this PRD.
