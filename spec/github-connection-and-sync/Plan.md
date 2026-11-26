# Plan: GitHub connection and scheduled data sync

**Status:** Reviewed 2026-11-26. Slices 1 to 5 built and waiting for your review; slice 6 not started.
**Spec:** [spec.md](./spec.md)
**Date:** 2026-11-25

This plan follows the loop in `.github/copilot-instructions.md`. It lists the slices in order, the files each slice touches, new dependencies, schema changes, the decisions the spec left to the plan, and the risks. After each slice I stop and wait for you.

---

## 1. What exists today

| Area | State |
|---|---|
| Backend | FastAPI skeleton. [config.py](../../backend/app/config.py) (pydantic-settings, reads the root `.env`), [db.py](../../backend/app/db.py) (async engine, `Base`, `get_db`), [main.py](../../backend/app/main.py) (`/health` only, CORS allows `GET` only). Alembic is set up in `backend/migrations` but has **no models and no revisions**. |
| Dependencies | `requirements.txt`: fastapi, uvicorn, pydantic-settings, sqlalchemy[asyncio], asyncpg, alembic. No Celery, Redis, httpx, JWT, or pytest. |
| Compose | [docker-compose.yml](../../docker-compose.yml) has **only `db`** (Postgres 16). No api, frontend, redis, worker, or beat. No Dockerfiles. |
| Frontend | Vite, React 19, TypeScript. Only a static `Landing` page ([Landing.tsx](../../frontend/src/Landing.tsx)), a hard-coded sidebar in [App.tsx](../../frontend/src/App.tsx), and a `/health` call in [api.ts](../../frontend/src/api.ts). No router, no charts, no tests. |
| Design mocks | `docs/03 · Connect GitHub.png`, `05 · Select repositories.png`, `07 · Overview.png`, `16 · Loading overview.png`, `17 · Empty repositories.png`, `18 · Connection error.png`. I will use them as visual reference in the UI/UX pass. The spec decides behaviour where they differ. |

Things I noticed that you should know about:

1. **Landing copy contradicts the spec.** It says "90 days of context" and "webhook updates"; the spec says all history and webhooks are Later. The sidebar links "CI/CD insights" and "Technology insights" are also Later. I will fix the copy and show only MVP navigation in the signed-in area (small change in slice 1).
2. **Folder name.** The instructions say `specs/<feature>/`, but your spec is in `spec/`. I am following your path (`spec\github-connection-and-sync\`).
3. **Git working tree.** The old `specs/phase-02-*` files and `.github/prompts/...` show as deleted, and the `.github` instructions are modified. I will not touch any of that.
4. `backend/.env/` is a **virtualenv folder** named `.env`. The real env file is the root `.env`. The Docker build must ignore `backend/.env` (see `.dockerignore` below).

---

## 2. Architecture (how the spec maps onto the layer rules)

```text
Browser (React, same origin through the Vite proxy)  ->  /api/*  FastAPI
FastAPI router -> service -> repository -> PostgreSQL
                          -> GitHubClient -> GitHub (only from services running in Celery, plus auth/install callbacks)
Celery Beat -> dispatch task -> one sync task per connection (connection_id only)
Celery task -> SynchronizationService -> GitHubClient + repositories -> PostgreSQL
Dashboard endpoint -> pull_requests service -> repository -> PostgreSQL     (never GitHub)
```

### Backend modules (feature-oriented, matching the modules named in the instructions)

| Module | Owns | Notes |
|---|---|---|
| `identity` | users, sessions, OAuth state; sign-in, `me`, logout; `get_current_user` dependency | Knows nothing about connections. Authentication and the GitHub connection stay separate states. |
| `github_integration` | `GitHubClient`, app JWT, installation tokens, connections; install start and callback; connection status | The only code that talks to GitHub. Returns internal schemas, never raw GitHub payloads. |
| `repositories` | the repositories the App can access, selection state; list and save selection | |
| `pull_requests` | pull request rows; the widget read endpoint (summary) | |
| `synchronization` | Celery app, tasks, Beat schedule, `sync_runs`, the orchestration service, task dispatcher | Tasks are thin. Cross-module calls go **service to service**, never into another module's repository. |
| `common` | typed errors, token generation and hashing, structured logging with redaction, clock | Small. Only what two or more modules need. |

`config.py` and `db.py` stay where they are and get extended. Cross-module rule reminder: `synchronization.service` calls `repositories.service` and `pull_requests.service` (not their repositories). `github_integration.service` and `repositories.service` trigger syncs through an injected `SyncDispatcher` (a small protocol that calls `celery.send_task` by name, so there are no import cycles).

### Frontend structure

```text
frontend/src/
├── shared/ (api/http.ts, components/{AppShell,LoadingState,EmptyState,ErrorState})
└── features/
    ├── auth/         (api, hooks/useSession + context, pages/SignInPage, RequireAuth)
    ├── connection/   (api, pages/ConnectGitHubPage)
    ├── repositories/ (api, pages/SelectRepositoriesPage)
    └── dashboard/    (api, components/PullRequestWidget + chart, pages/DashboardPage)
```

State: React context for the session plus plain hooks. No state library (needs your OK if you want one).

---

## 3. Decisions the spec left to the plan

The spec says these are decided here and reviewed by you. Please check each one.

### 3.1 Sessions, cookies, CSRF

- **Session credential:** 32 random bytes (`secrets.token_urlsafe`), sent only in the cookie. Only its **SHA-256 hash** is stored.
- **Lifetime:** fixed **14 days** from sign-in, no sliding renewal (simple for MVP). Expired or revoked sessions are rejected on every request.
- **Cookie `devpulse_session`:** `HttpOnly`, `SameSite=Lax`, `Path=/`, `Max-Age` of 14 days, `Secure` when `ENVIRONMENT=production` (off in local dev because it runs on `http://localhost`).
- **Rotation:** every sign-in creates a brand-new session credential. If the request already carried a session cookie, that old session is revoked (prevents fixation).
- **Logout:** revokes only the current session row and clears the cookie. Other browsers stay signed in. Connection and data are untouched.
- **CSRF:** `SameSite=Lax` plus an **Origin check** on every unsafe method (`POST`, `PUT`, `PATCH`, `DELETE`): the `Origin` header must equal the configured frontend origin, otherwise 403. All state-changing endpoints take JSON only. The two GitHub redirect starts (`GET`) only create a single-use state row, so they are not state-changing for the user.
- **OAuth state:** 32 random bytes, stored **hashed** in `oauth_states` with a purpose (`sign_in` or `install`), 10-minute expiry, consumed on first use (single use, enforced with an atomic update). A second HTTP-only cookie `devpulse_oauth` carries a nonce whose hash is stored in the same row, so a callback from another browser is rejected (login-CSRF protection). Install state is also bound to the signed-in user.
- **Redirects after callbacks:** always to fixed in-app paths. Errors use a **fixed whitelist of codes** in the query string (`cancelled`, `invalid_state`, `github_unavailable`, `failed`, `installation_not_allowed`). No arbitrary `next` parameter, so no open redirects.

### 3.2 Same-origin in development (Vite proxy)

The browser talks only to the frontend origin (`http://localhost:5173`). Vite proxies `/api` and `/health` to the API (`http://api:8000` inside Compose). Effects:

- The cookie is first-party for the frontend, so no cross-origin cookies and no CORS credentials setup.
- The GitHub App callback and setup URLs are `http://localhost:5173/api/...`.
- [api.ts](../../frontend/src/api.ts) switches from the absolute `VITE_API_BASE_URL` to relative URLs. This changes an existing file, so please confirm.

### 3.3 GitHub App and permissions

One GitHub App for both sign-in and installation (spec assumption). Registration is a manual step by you; I will give exact values in the slice 1 summary.

| Setting | Value |
|---|---|
| Repository permissions | **Metadata: read** (mandatory) and **Pull requests: read**. Nothing else. |
| Account permissions | **None.** Email is taken only from the public profile (`GET /user`) if GitHub provides it, so the "email" permission is not needed. |
| Webhook | **Inactive** (webhooks are Later). Removal of the App is detected by the next sync run, as the spec describes. |
| User tokens | Used once at sign-in to read `/user`, then discarded. Never stored. |
| Callback URL (sign-in) | `http://localhost:5173/api/auth/github/callback` |
| Setup URL (after install) | `http://localhost:5173/api/github/install/callback`, with "Redirect on update" on |
| "Request user authorization during installation" | **Off** |
| Install target | "Any account", but the callback only accepts the user's own **personal** account (see 3.4) |
| Installation tokens | Minted per run from an app JWT (RS256, 9-minute lifetime), **requested with only `pull_requests: read` and `metadata: read`**, held in memory for the run, never stored or logged. |
| Private key | A `.pem` file outside the database, mounted read-only into the api and worker containers. `*.pem` is already git-ignored. I will also ignore a `secrets/` folder. |

### 3.4 Installation callback ownership check

The `installation_id` in the setup callback comes from the browser, so it cannot be trusted by itself. The callback requires all of these:

1. A valid, unused `install` state tied to the signed-in user and the nonce cookie.
2. `GET /app/installations/{id}` using the app JWT (no user token needed). The response must show `account.type == "User"` and `account.id == the signed-in user's GitHub user ID`.
3. The installation is not already linked to a different DevPulse user (unique constraint on `installation_id`).

Anything else redirects to `/connect?error=installation_not_allowed` without saying why. This fits "personal accounts only, one connection per user" and avoids storing a user token.

### 3.5 How the all-history fetch is split across runs

**Decided (2026-11-26): REST only**, for both the repository list and pull requests. The list call `GET /repos/{owner}/{repo}/pulls?state=all` gives state, draft flag, title, author, branch and dates, 50 per page. Review state needs one extra call per pull request, `GET /repos/{owner}/{repo}/pulls/{number}/reviews`.

**Decided (2026-11-26): two phases, so the history import stays fast.** The widget only needs pull request counts plus review state for *open* pull requests (3.8), so reviews are not fetched page by page.

- **Phase 1, import pull requests:** list pages only (50 per call). State, draft flag, title, author, branch and dates are saved with the page cursor in one transaction. `review_state` stays empty ("not loaded yet") and counts appear as soon as phase 1 has run.
- **Phase 2, fill in review state:** a second pass over pull requests whose reviews are not loaded, or whose `updated_at` changed since they were loaded. Order: open pull requests first, then closed or merged ones, newest first. Each pull request's result is saved right after its call, so progress is kept per pull request and resumes in the next run.
- **Budget:** phase 1 for all selected repositories gets the budget first, then phase 2 with what is left. Both stop at the same run limits (below).

- **Per repository state:** `backfill_cursor` (the next page number), `backfill_started_at`, `backfill_completed_at`, `incremental_watermark`, `last_synced_at`.
- **Backfill (phase 1):** `sort=created&direction=asc`, oldest first, 50 per page. This keeps page numbers stable between runs (new PRs only append at the end).
- **After backfill completes:** `incremental_watermark = backfill_started_at`, so PRs changed during the long backfill are caught by the next incremental pass.
- **Incremental runs:** `sort=updated&direction=desc`, stop at the first PR older than `watermark - 5 minutes`, then set the watermark to this run's start time. Pull requests found changed go to phase 2.
- **Run budget:** a task stops cleanly (run status `partial`) when it has used about 8 minutes, or the `X-RateLimit-Remaining` header reports fewer than 200 requests left. The next 15-minute run continues from the saved cursor. Repositories are processed oldest-synced first, so one huge repository cannot starve the others. A repository that is unselected while a run is in progress is skipped from the next page onward.
- **Celery limits:** soft limit 540 s, hard limit 600 s.
- **Reselecting** a repository resumes: unfinished backfill continues from its cursor, finished backfill runs an incremental pass from its old watermark (catching up on what changed meanwhile).

### 3.6 Review state

The reviews endpoint returns every review event, so `review_state` is derived: take each reviewer's latest `APPROVED` / `CHANGES_REQUESTED` / `DISMISSED` review; `changes_requested` if any reviewer's latest opinion requests changes, else `approved` if any approves, else `commented` if there are any reviews, else `none`. Pull request state is `open`, `closed` (not merged), or `merged`; `is_draft` is kept too.

**Stored (decided 2026-11-26):** title, author login, head branch name, state, draft flag, review state, and key dates. **Not stored:** PR bodies, comments, file names, source code. Author is stored for display only: no endpoint or widget may group, rank, or compare by author (non-goal), and the widget shows only counts over time.

### 3.7 Retry timings and rate limits

| Case | Behaviour |
|---|---|
| Temporary (GitHub 5xx, timeout, network) | Retry with exponential backoff and full jitter: base 60 s, doubling, capped at 15 min, **at most 5 retries** (roughly 1, 2, 4, 8, 15 min). After that the run is `failed` and the next 15-minute beat tries again. |
| Rate limit (`429`, or `403` with exhausted limit, or `X-RateLimit-Remaining` low) | If the reset is within 15 min, retry at reset plus jitter. If it is later, end the run as `rate_limited`, store `rate_limited_until` on the connection, and let Beat skip that connection until then. |
| Revoked or missing access (installation `404`, suspended, `401`, or `pull_requests` permission missing) | **No retry.** Connection becomes `needs_attention` with a safe reason (`access_revoked`, `permission_missing`, `suspended`). Beat skips non-`active` connections. |
| Unexpected error | One retry, then `failed` with category `unexpected`. Details only in logs (redacted), never in API responses. |

Recovery for `needs_attention` in the MVP: the user fixes it on GitHub and goes through the install link again. The install callback is idempotent for the same installation and sets the status back to `active`. (A full disconnect or reconnect is Later.)

### 3.8 Widget time grouping

- Weekly buckets, **UTC, Monday start** (`date_trunc('week', ...)`), default window **12 weeks**, selectable as **4, 12, 26 or 52 weeks** (`?weeks=` 1 to 52 is accepted by the API).
- Per week: pull requests **opened** (by `created_at`) and **merged** (by `merged_at`). Pull requests by bots are included; draft pull requests count as open.
- Summary numbers: open now, opened in the window, merged in the window, and open PRs by review state (including "not loaded yet" while the review pass is catching up).
- All calculated in SQL in the backend. React only draws. The widget states its scope ("N selected repositories, last 12 weeks, UTC") and uses neutral wording, with no productivity or comparison language.
- The chart has a text alternative (a data table) for accessibility.

### 3.9 Freshness and "out of date"

- `last_updated_at` = the last time a pull request sync run for the connection **succeeded** (UTC).
- `is_stale` is true if the most recent run failed, or `last_updated_at` is older than 45 minutes (3 missed intervals).
- `history_complete` is false while any selected repository still has an unfinished backfill, so the widget can say "Importing history: 2 of 5 repositories".

### 3.10 Docker Compose layout

| Service | What | Notes |
|---|---|---|
| `db` | Postgres 16 (exists) | Unchanged. |
| `redis` | `redis:7-alpine` | Healthcheck. Broker and result backend for Celery. |
| `migrate` | one-shot: `alembic upgrade head` | `api`, `worker`, `beat` wait for it to complete successfully. |
| `api` | FastAPI with uvicorn | Port 8000. |
| `worker` | `celery -A app.synchronization.celery_app worker` | Prefork on Linux. Concurrency 2. |
| `beat` | `celery -A app.synchronization.celery_app beat` | **Exactly one instance.** Schedule file in a named volume. |
| `frontend` | Vite dev server in Node 22 | `--host`, proxies `/api` to `api:8000`. |

New files: `backend/Dockerfile` (python 3.12-slim, matching your local 3.12 venv), `frontend/Dockerfile`, `.dockerignore` for both (excluding `backend/.env`, `node_modules`, `dist`, `__pycache__`). All services read the root `.env`; compose overrides `POSTGRES_HOST=db` and sets `REDIS_URL`. Celery prefork does not run on native Windows, so Docker is the supported way to run the worker (otherwise `--pool=solo`).

### 3.11 Celery with an async backend

Celery tasks are synchronous, but our services and repositories are async. Each task runs `asyncio.run(service.method(...))` and builds its **own** async engine with `NullPool` for that run. The module-level pooled engine in [db.py](../../backend/app/db.py) is only for the API process (reusing it across `asyncio.run` calls breaks because pooled connections are tied to a closed event loop). This keeps one code path for repositories rather than a sync and an async copy.

### 3.12 Idempotency and duplicate delivery

- **Upserts:** `INSERT ... ON CONFLICT DO UPDATE` on `(repository_id, number)` for pull requests, `(connection_id, github_repo_id)` for repositories, `github_user_id` for users.
- **One run per connection at a time:** a partial unique index on `sync_runs(connection_id) WHERE status = 'running'`. A second task that cannot insert its `running` row exits quietly. A `running` row older than 20 minutes (crashed worker) is marked `failed (abandoned)` and replaced.
- **Enqueue after commit**, never before, so a task can never run ahead of the data it needs. If Redis is down at that moment, the error is logged and the next 15-minute beat picks the work up (the saved selection is not lost).
- **Task arguments:** `connection_id` (UUID string) and a `trigger` label only. Never credentials.

---

## 4. Data model (Alembic, one migration per slice)

| Table | Key columns | Constraints and indexes |
|---|---|---|
| `users` | id (uuid), `github_user_id` (bigint), login, name, avatar_url, email (nullable), created_at, updated_at, last_login_at | unique `github_user_id` |
| `sessions` | id, user_id, `token_hash`, created_at, expires_at, revoked_at | unique `token_hash`; index user_id; FK cascade |
| `oauth_states` | id, `state_hash`, `nonce_hash`, purpose, user_id (nullable), expires_at, consumed_at | unique `state_hash`; index expires_at |
| `github_connections` | id, user_id, `installation_id` (bigint), github_account_id, github_account_login, account_type, permissions (jsonb), status (`active` / `needs_attention`), status_reason, last_checked_at, last_successful_sync_at, rate_limited_until, repositories_synced_at, created_at, updated_at | unique `user_id` (one per user); unique `installation_id` |
| `repositories` | id, connection_id, `github_repo_id`, owner_login, name, full_name, is_private, is_available, is_selected, selected_at, backfill_cursor, backfill_started_at, backfill_completed_at, incremental_watermark, last_synced_at | unique `(connection_id, github_repo_id)`; index `(connection_id, is_selected)` |
| `pull_requests` | id, repository_id, github_pr_id, number, state, is_draft, title, author_login, head_branch, review_state, created_at_gh, updated_at_gh, closed_at, merged_at, fetched_at | unique `(repository_id, number)`; indexes `(repository_id, created_at_gh)`, `(repository_id, merged_at)`, `(repository_id, state)`; FK cascade |
| `sync_runs` | id, connection_id, kind (`repository_list` / `pull_requests`), trigger (`connected` / `selection_saved` / `schedule`), status (`running` / `succeeded` / `partial` / `failed` / `rate_limited`), started_at, finished_at, error_category, repositories_total, repositories_completed | partial unique index one `running` per connection; index `(connection_id, started_at desc)` |

Notes:

- Repositories also store only the sync progress needed for backfill. No source code, no PR bodies or comments.
- The `repositories` backfill columns and `pull_requests` / `sync_runs` arrive in slice 4's migration, so each slice creates only what it needs.
- "Unselect" sets `is_selected = false`; rows are kept. Queries for the widget and for fetching always filter on `is_selected AND is_available`.
- A repository that disappears from the installation gets `is_available = false` (hidden, not fetched, data kept).
- Ownership: every repository method takes `user_id` or `connection_id` and joins through `github_connections.user_id`. Services enforce it too. A wrong-owner ID looks the same as a missing one (404, no leak).
- Times are `timestamptz` in UTC. The API sends ISO-8601 UTC; the UI labels them "UTC".

---

## 5. API (all under `/api`; routers stay thin, Pydantic response models only)

| Method and path | Auth | Purpose |
|---|---|---|
| `GET /api/auth/github/login` | none | Create state and nonce cookie, 302 to GitHub authorize |
| `GET /api/auth/github/callback` | none | Validate state, exchange code in memory, read `/user`, upsert user by GitHub ID, create session, set cookie, 302 to `/start` (or `/sign-in?error=<code>`) |
| `GET /api/auth/me` | session | `{id, login, name, avatar_url, email}`; 401 when not signed in |
| `POST /api/auth/logout` | session + Origin check | Revoke this session, clear cookie, 204 |
| `GET /api/github/install` | session | Create install state, 302 to `github.com/apps/<slug>/installations/new?state=...` |
| `GET /api/github/install/callback` | session | Validate (3.4), upsert connection, enqueue repository-list sync, 302 to `/repositories` (or `/connect?error=<code>`) |
| `GET /api/github/connection` | session | `{status: not_connected / active / needs_attention, reason, account_login, connected_at, last_checked_at, repositories_synced_at, repository_count}`. `not_connected` is a normal 200. |
| `GET /api/repositories?page&page_size&q` | session | `{list_status: syncing / ready, refreshed_at, total, selected_count, items:[{id, full_name, is_private, is_selected}]}`, page size default 50 and max 100 |
| `POST /api/repositories/selection` | session + Origin check | Body `{select:[id], unselect:[id]}` (deltas work with pagination). Validates ownership and availability, saves, enqueues a pull request sync if anything was newly selected. Returns the new `selected_count`. |
| `GET /api/pull-requests/summary?weeks=12` | session | Widget data (3.8 and 3.9): `last_updated_at`, `is_stale`, `history_complete`, `history_progress`, `repository_count`, `totals`, `open_by_review_state`, `weekly[]` |

No endpoint returns a token, a session value, or a raw GitHub payload. Error bodies are `{code, message}` with fixed safe messages.

Configuration added (placeholders only in `.env.example`; real values only in the untracked `.env`): `GITHUB_APP_ID`, `GITHUB_APP_SLUG`, `GITHUB_APP_CLIENT_ID`, `GITHUB_APP_CLIENT_SECRET`, `GITHUB_APP_PRIVATE_KEY_PATH`, `FRONTEND_BASE_URL`, `REDIS_URL`, `SESSION_LIFETIME_DAYS`, `SYNC_INTERVAL_SECONDS` (default 900). `ENVIRONMENT=production` turns on `Secure` cookies.

---

## 6. Slices

Each slice is a vertical, working step: code, tests, and migration together, then a review stop. The spec is itself the MVP, so slice 1 is the thinnest working start (sign-in on a running Compose stack) and each later slice adds one visible capability.

### Slice 1: Sign in with GitHub (identity) and the Compose base

**Result:** `docker compose up` starts db, migrate, api and frontend. You click "Continue with GitHub", return signed in, stay signed in after a refresh, and can log out.

- Backend: `identity` module (models, repository, service, router, dependencies), minimal `GitHubClient` (code exchange, `GET /user`), `common` (errors, token and hash helpers, JSON logging with redaction, request ID middleware, Origin check), config additions, CORS adjusted, `/api` prefix, first Alembic revision (`users`, `sessions`, `oauth_states`), import models in `migrations/env.py`.
- Frontend: install `react-router-dom`; routes `/`, `/sign-in`, `/start`, protected area; `AuthProvider` using `/api/auth/me`; `SignInPage` (loading, error with whitelisted codes, retry); small signed-in shell with logout; fix Landing copy and sidebar; Vite proxy; relative API base.
- Infra: Dockerfiles, `.dockerignore`, compose services `migrate`, `api`, `frontend`; `.env.example` update.
- Tests: scenarios "new user signs in", "returning user, no second user", "sign-in cancelled or fails (invalid or reused state)", "I log out (two browsers)"; session expiry and revocation; cookie attributes; no token in responses or logs; raw session value not persisted; GitHub client with mocked HTTP (missing email, renamed user). Frontend: sign-in page states, route protection, logout.
- **Needs from you before I start:** the GitHub App registered (values in 3.3) and its client ID and secret in `.env`.
- **Note:** after sign-in the user lands on a temporary signed-in page, because the connect page arrives in slice 2.

### Slice 2: Connect GitHub and fetch the repository list (introduces Celery and Redis)

**Result:** A signed-in user with no connection lands on the connect page, installs the App, returns to DevPulse, sees status "connected", and the repositories the App can access are stored in PostgreSQL by a background job.

- Backend: `github_integration` (app JWT, installation token, installation lookup, list installation repositories with pagination and rate-limit reading, error mapping), `connections` model and service (install start and callback with the 3.4 checks, status endpoint), `repositories` module (models, upsert from the list, `is_available` handling), `synchronization` skeleton (Celery app, `SyncDispatcher`, `sync_repository_list` task, `sync_runs` for the repository-list kind), Alembic revision 2.
- Infra: compose `redis` and `worker`; `.env`: `REDIS_URL`, private key mount.
- Frontend: `ConnectGitHubPage` (not connected, connected, needs-attention, loading, error), post-sign-in routing (`/start`: no connection to `/connect`).
- Tests: scenario "I connect my GitHub account" (belongs to me only); installation owned by someone else rejected; reused or invalid install state; duplicate callback creates no duplicate rows; repository upsert idempotency and pagination (fixtures); task receives only `connection_id`; installation `404` marks `needs_attention`; no tokens in logs or responses.
- **Built (2026-11-26), where it differs from the text above:**
  - After a successful install the callback redirects to `/connect` (not `/repositories`, which arrives in slice 3). Slice 3 changes that one redirect.
  - `/start` now always redirects to `/connect`; slice 5 will send connected users to the dashboard instead.
  - No Celery result backend: job state lives in `sync_runs`, so Redis is broker only.
  - Retry delay uses half-fixed plus half-random jitter (45 s, 90 s, ... capped at 15 min) so a retry never fires immediately.
  - `sync_runs` and `github_connections` got only the columns slice 2 needs; the rest arrive with slice 4.
  - GitHub's "Redirect on update" sends no `state`. That case is accepted only for an installation that is already the user's own connection (it just refreshes the repository list). **Not yet checked against a real GitHub installation.**
  - Worker logs go through the same JSON and redaction setup as the API.
  - `app/AppShell.tsx` (sidebar layout from slice 1) is unused until the dashboard slice.

### Slice 3: Repository selection

**Result:** The user sees their repositories, picks which to track, saves, and can change the selection later.

- Backend: list (search and pagination) and selection endpoints; ownership and availability validation; unselect keeps data. The "enqueue sync" hook is added here but the PR sync task itself lands in slice 4, so in this slice a save only persists the selection.
- Frontend: `SelectRepositoriesPage` (loading, "still fetching repositories" with polling, empty, error, search, pending changes kept after a failed save).
- Tests: scenarios "I choose which repositories to track" (selection part) and "I stop tracking a repository"; cross-user selection attempts rejected; unselect then reselect keeps the same row; selecting an unavailable repository rejected.
- **Built (2026-11-26), where it differs from the text above:**
  - No "enqueue sync" hook yet: an unused hook would be dead code, so slice 4 adds the call where it is needed (after a save that newly selects something).
  - The install callback now redirects a healthy connection to `/repositories`; a connection that needs attention stays on `/connect`.
  - The list shows only repositories the App can still access. `selected_count` counts selected and available ones. A repository that is hidden because it left GitHub keeps its selection and gets it back if it returns.
  - Unselecting is always allowed (even for a repository that disappeared), so it can be dropped; selecting needs the repository to be available. Unselecting clears `selected_at`.
  - A save is all or nothing, and a repository that is not yours looks like one that does not exist (404).
  - Limits: 500 changes per save, page size at most 100, search text at most 100 characters.
  - Not built (not in the plan): an "only selected" filter and language / last-updated columns from the mockup.

### Slice 4: Scheduled pull request sync (the core background job)

**Result:** Saving a selection fetches pull request data right away, then every 15 minutes, with no duplicates, resumable history import, retries, and a `needs attention` stop. Visible via the database (and the existing connection status); the widget comes next.

**Decisions for this slice (2026-11-26):**

- **Two-phase fetch** (3.5): pull requests first, review state in a second pass, open pull requests first.
- **Schedule covers all active connections** (not only those with a selection). Each run always refreshes the repository list so new repositories reach the selection page, and fetches pull requests only for selected repositories. Connections that need attention or are rate limited are skipped.
- **A job skipped because another is running is retried soon:** when a job started by connecting or by saving a selection finds one already running for that connection, it re-queues itself every ~30 seconds, up to 5 times, instead of waiting for the next scheduled run. Scheduled jobs that find one running just exit.
- **Pull requests by bots are counted** like any other. The author is stored for display only and is never used to group or filter.
- **Draft pull requests count as open.** `is_draft` is stored.
- Interval and run budget are settings (`SYNC_INTERVAL_SECONDS`, default 900), so the multi-run behaviour can be tried with small values.

- Backend: REST pull request and review calls in `GitHubClient` (pagination, rate-limit headers), `pull_requests` module (model, upsert repository), `synchronization.service` (repository-list refresh, then PR sync with backfill and incremental per 3.5; run lock per 3.12; retry and classification per 3.7), Celery Beat schedule `dispatch_due_syncs` every 900 s (active connections with at least one selected and available repository), `sync_pull_requests` task, wire the selection save to enqueue, `sync_runs` for the PR kind, Alembic revision 3 (also adds the repository sync-state columns).
- Infra: compose `beat` plus schedule volume.
- Tests: scenarios "scheduled job stores PR data" and "running again creates no duplicates"; "GitHub temporarily unavailable" (earlier data kept, retry scheduled); "Access is removed on GitHub" (no retry, needs attention); partial run resumes from cursor; run budget respected; rate-limit handling; duplicate or concurrent delivery safe (second task exits); re-select resumes; due-connection selection (skips needs-attention, rate-limited, nothing selected); Celery args contain no credentials; bounded retries. PostgreSQL integration tests for the unique constraints, the upserts, and the single-running-run index.
- **Built (2026-11-26), where it differs from the text above:**
  - Two tasks now exist: `sync.repository_list` (used right after connecting) and `sync.pull_requests` (refreshes the repository list, then imports pull requests). Both share one run lifecycle and the one-running-job-per-connection rule. `sync.dispatch_due` is what Beat runs.
  - A partial run (budget used up) counts as a successful update for `last_successful_sync_at`. A failed run does not.
  - `sync_runs` did not get `repositories_total` / `repositories_completed`; "Importing history: 2 of 5" in slice 5 is derived from the repositories' own `backfill_completed_at`.
  - New settings: `SYNC_INTERVAL_SECONDS` (900), `SYNC_RUN_BUDGET_SECONDS` (480), `SYNC_RATE_LIMIT_RESERVE` (200), `SYNC_RUN_MAX_REQUESTS` (0 = no cap).
  - A pull request whose repository returns 404 hides just that repository (`is_available = false`); it does not mark the whole connection as needing attention.
  - A job queued by connecting or saving a selection that finds another job running retries every 30 s up to 5 times; a scheduled job just exits.
  - Compose gets a `beat` service with its schedule file in a named volume. **Run exactly one Beat.**
  - Checked live against real GitHub (throwaway database, Beat on a 10-second interval): scheduled runs succeeded, 38 repositories' histories completed, review state filled in.

### Slice 5: Dashboard with the pull request widget

**Result:** The dashboard shows the pull request widget from the database, with a "last updated" time, and guides the user when there is nothing to show. Post-sign-in routing is complete (connection to `/dashboard`).

**Decisions for this slice (2026-11-26):**

- **Time window selector now:** the dashboard has a selector with **4, 12, 26 and 52 weeks** (default 12), which sets `?weeks=` on the summary endpoint. The chosen window and "UTC" are shown with the chart.
- **Chart:** grouped bars per week, **opened** and **merged** side by side (ECharts), with a text table of the same numbers as the accessible alternative. The current week is marked "in progress".
- **Navigation:** the dashboard uses the sidebar layout from mockup 07 with **Overview**, **Repositories** (the selection page) and **GitHub connection** (the connect page), plus a small status block (connection state, repository count, last updated). The selection and connect pages get a **Back to dashboard** button once the user has a connection.
- **Problems are shown on the dashboard, not by redirecting:** when the connection needs attention or the data is out of date, a warning banner sits above the data (which stays visible) with a link to fix it.
- **Updates while the first import runs:** the dashboard re-checks every 30 seconds while data is incomplete (importing history, or nothing yet) for up to 5 minutes, then stops and shows a "reload" prompt. No manual "refresh now" button (Later).
- **No per-repository breakdown:** totals across the selected repositories only. The widget states its scope ("N selected repositories, last 12 weeks, UTC") and uses neutral wording.
- **Routing after sign-in:** no connection goes to `/connect`; a connection (including one that needs attention, or with nothing selected) goes to `/dashboard`, which shows the matching prompt.

- Backend: summary endpoint, SQL aggregation, freshness fields (3.9).
- Frontend: install `echarts`; `DashboardPage`, `PullRequestWidget` with chart and text table, "last updated (UTC)", states: loading, no connection (prompt), nothing selected (prompt), empty (selected, no PRs yet), importing history (partial), out of date (stale banner), needs attention, error with retry.
- Tests: scenarios "dashboard guides me", "widget reads from the database" (verified: no GitHub client is called in the request path), "I only see my own data", stale marking, unselected repositories excluded and returning on reselect; frontend state tests and "no credentials in rendered content or browser storage".
- **Built (2026-11-26), where it differs from the text above:**
  - The summary endpoint (`GET /api/pull-requests/summary?weeks=N`) also returns the connection state (`not_connected`, `active`, `needs_attention`), so the dashboard needs one call to decide between the connect prompt, the select prompt and the data. A user without a connection gets a normal 200, not an error.
  - "Out of date" = the most recent finished pull request run **failed or was rate limited** (marked at once), or the last update is older than **3 x `SYNC_INTERVAL_SECONDS`** (45 minutes by default). A partial run is not a failure. Read through a small read-only `SyncStatusService` so the dashboard never touches the synchronization tables directly.
  - `history_complete` is true when nothing is selected (there is nothing to wait for).
  - The sidebar status block shows connection state and the number of repositories the App can access (from the existing connection endpoint). The last-updated time is shown on the page itself instead.
  - The chart library is a separate lazy-loaded chunk (about 507 kB, 171 kB compressed); the main bundle stays at about 300 kB. Vite warns about the chunk size; I left the warning as is.
  - The chart is replaced by a stand-in in the unit tests (the test environment has no canvas). It was checked visually in a real browser against a mock API instead.
  - The setup pages (connect, repositories) have a "Back to dashboard" button; on the connect page it only appears once there is a connection.

### Slice 6: Hardening and acceptance

- Playwright end-to-end tests are **out of scope** (decided 2026-11-26). Key journeys are covered by React Testing Library and API integration tests.
- Security sweep against the "Security assertions" list in the tests instructions; log redaction test across the sync path.
- README run section (GitHub App setup, `.env`, `docker compose up`, running tests), and verifying every acceptance criterion below, including a clean `docker compose up` from scratch.
- Your UI/UX pass items come after this review.

---

## 7. Traceability

### Scenarios to slices

| Scenario | Slice |
|---|---|
| New user signs in; returning user; sign-in cancelled or fails; I log out | 1 |
| I connect my GitHub account | 2 |
| I choose which repositories to track; I stop tracking a repository | 3 (selection) and 4 (fetching) |
| The scheduled job stores pull request data; GitHub temporarily unavailable; Access is removed on GitHub | 4 |
| Dashboard guides me; widget reads from the database; I only see my own data | 5 (ownership is tested in every slice) |

### Acceptance criteria to slices

| Criterion | Slice |
|---|---|
| Sign in, still signed in after refresh | 1 |
| Landing: connect page without connection, dashboard with one | 2 (connect page) and 5 (dashboard) |
| Connect and see status; see repositories and pick | 2, 3 |
| PR data right after save, then every 15 min, no duplicates | 4 |
| Whole history, several runs, rate limits, progress kept | 4 |
| Unselect hides and stops; data kept and returns | 3, 4, 5 |
| Widget from the database with last updated; dashboard never calls GitHub | 5 |
| GitHub failure keeps earlier data, marked out of date, safe errors | 4, 5 |
| Another user's data never visible | every slice |
| No secret in logs, responses, URLs, or browser storage | every slice, swept in 6 |
| `docker compose up` starts all six services plus migrate | built up in 1, 2, 4, checked in 6 |
| Tests pass | every slice |

---

## 8. New dependencies (need your OK, per the instructions)

All are within the approved stack except where noted.

**Backend runtime:** `celery[redis]` (Celery plus the Redis client), `httpx` (GitHub HTTP client; it is already installed in your venv indirectly but is not in `requirements.txt`), `PyJWT[crypto]` (sign the GitHub App JWT; it uses `cryptography`).

**Backend dev (new `requirements-dev.txt`):** `pytest`, `pytest-asyncio`. HTTP mocking uses `httpx.MockTransport`, and Celery uses its test mode, so no extra mocking libraries. Integration tests use the Compose Postgres with a separate `devpulse_test` database.

**Frontend runtime:** `react-router-dom`, `echarts`.

**Frontend dev:** `vitest`, `jsdom`, `@testing-library/react`, `@testing-library/user-event`, `@testing-library/jest-dom`. No Playwright (decided). No `msw`: tests stub `fetch` by hand at the network boundary, which is one fewer dependency.

**Not adding:** a state library, a JSON-logging library (a small stdlib formatter is enough), an email validator, any scheduler other than Celery Beat.

---

## 9. Risks and how the plan handles them

| Risk | Handling |
|---|---|
| Large repositories exhaust GitHub rate limits | REST costs about one call per PR on the first fetch, so: reviews fetched only for new or changed PRs, per-page commits, run budget, reserve of 200 requests, `rate_limited_until`, oldest-synced-first fairness (3.5, 3.7). |
| Sync progress lost or duplicated | Cursor and upsert in one transaction; unique `(repository_id, number)`; single running run per connection. |
| A forged `installation_id` links someone else's installation | Ownership check in 3.4 (account ID must equal your GitHub ID), unique `installation_id`, state bound to the user and a nonce cookie. |
| Redis down when saving a selection | Selection is saved first; enqueue failure is logged; the next beat picks it up. UI shows "waiting for first sync". |
| Async code inside Celery | Per-task engine with `NullPool` (3.11); covered by a task-level test. |
| `reviewDecision` is empty without branch rules | Derived review state (3.6). |
| PR updated while a long backfill runs | Watermark set to backfill start (3.5). |
| Setup callback behaviour differs from my reading of the docs (GitHub Apps with `setup_action=update`, "Redirect on update") | I will verify with a real installation in slice 2 and report any difference before building on it. |
| Existing Landing copy and sidebar promise non-MVP features | Fixed in slice 1 (section 1). |
| A secret leaking through logs or errors | Redaction filter on the logger, fixed safe error bodies, tests that scan logs and responses for token patterns. |
| Windows developer machine cannot run Celery prefork | Docker is the supported path; documented. |

---

## 10. Decisions (reviewed 2026-11-26)

Result: items 1, 2, 4, 5, 6, 7, 8 kept as written. **Item 3 changed to REST only. Item 9 changed to store title, author, and head branch. Playwright dropped. `msw` not used.** The original list follows; items 3 and 9 are superseded by sections 3.5 and 3.6.

1. **Vite proxy and same-origin cookies** (3.2), including changing [api.ts](../../frontend/src/api.ts) to relative URLs.
2. **Installation ownership check by account ID** instead of storing a user token or asking for authorization during install (3.4).
3. **GraphQL for pull requests**, REST for the repository list (3.5).
4. **14-day fixed session** (3.1).
5. **Weekly UTC buckets, 12-week default window**, plus the summary numbers listed in 3.8.
6. **Selection API uses deltas with a paginated list** (section 5). A simpler alternative is "send the whole selected set" with no pagination, fine for tens of repositories but awkward for hundreds.
7. **The new dependencies** in section 8, and whether to use `msw`.
8. **Slice order and sizes** (section 6), in particular that slice 3 only saves the selection and slice 4 makes it trigger fetching.
9. **Stored PR fields** (3.6): no titles, authors, or branch names. Say so if you want any of them.

I will not start slice 1 until you review this plan and tell me which of these to change.
