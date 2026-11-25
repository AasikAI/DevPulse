# Phase 2: GitHub Authentication and Connection: Requirements Specification

| | |
|---|---|
| Status | **DRAFT, revision 2. Awaiting requirements approval** |
| Phase | 2 of 12 (PRD section 17) |
| Inputs read | `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md`, `docs/PRD.md` (sections 11.1, 11.2, 14.1, 15, 17, 23), `docs/phase_0/spec.md`, `docs/phase_1/spec.md`, repository structure, Figma exports in `docs/*.png` (screens 03, 04, 18 for context), `revise-phase-2-requirements-001.md`, `revise-phase-2-requirements-002.md` |
| Companion files | `assumptions.md`, `open-questions.md`, `requirements-bdd-coverage.md`, `features/*.feature.md` |
| Documentation only | No code, migration, Compose, dependency, test or design file is created by this package |

Requirement markers: **Priority** is Must, Should or Could. **Source** is `Intent` (owner's stated intent), `Handoff` (decision in the phase prompt), `PRD` (matches a PRD requirement; the PRD ID is kept as an alias), `Decision A#` (owner decision in revision 1), `Revision 1, B#` (owner-directed spec fix), `Decision R2-#` (owner decision in revision 2) or `[INFERRED]` (the author's inference, open to challenge). **`[REV1]`** and **`[REV2]`** mark every requirement added or changed in revision 1 and revision 2. A requirement that no longer applies stays in place and is marked `RETIRED`.

## Revision history

| Revision | Date | Summary |
|---|---|---|
| 0 | 2026-11-23 | Initial requirements package |
| 1 | 2026-11-24 | Owner decisions A1 to A13 recorded; spec fixes B1 to B8; feature fixes C1 to C12; feature files converted to `.feature.md`; bookkeeping files regenerated. Every changed or added item carries `[REV1]` (requirements) or `@REV1` (scenarios) |
| 2 | 2026-11-24 | Revision 2: owner decisions R2-1 to R2-12 recorded; mechanical fixes B1 to B3; Installation required no longer expires; actions per state settled; repository access in Permission attention required left unspecified (OQ-025); reactivation, rejection and organisation-callback outcomes added; new open questions OQ-024 to OQ-028. Every changed or added item carries `[REV2]` (requirements) or `@REV2` (scenarios) |

---

## 0. Preconditions

- **P-1. Phase 1 completion comes first.** The repository lacks several Phase 1 foundations: React Router, Tailwind CSS, Apache ECharts, Vitest, React Testing Library, Playwright, pytest, a backend tests folder and a CI workflow (assumption A-001). By owner decision A1 (revision 1), these are closed in a separate "Phase 1 completion" step with its own approval, **before** Phase 2 implementation starts. This package does not specify that work.
- **P-2. Same-site deployment.** By owner decision A12 (OQ-022), the frontend and the backend are served from the same site. The open design questions about cookies and forgery protection (OQ-003 and OQ-013) must assume this.
- **Design guidance (owner, revision 2; guidance, not a requirement).** Actions and flows must be standard and reliable, and must not be over-engineered. No action, state or screen is added beyond those stated in this package.

## 1. Purpose

DevPulse needs a trustworthy foundation before any GitHub data can be shown. Phase 2 lets a person prove who they are using GitHub, gives DevPulse a local user and a protected application session, shows that person's GitHub profile in its own Profile section, and lets them configure and manage a verified GitHub App connection in a Tool Configuration area. Later phases rely on this connection being verified and owned by exactly one DevPulse user.

## 2. Scope

In scope (phase prompt section 4, as revised):

1. GitHub user authorization used as DevPulse authentication ("Continue with GitHub")
2. Creating or updating the local user, keyed by the stable GitHub user ID
3. Persisting authorized GitHub profile metadata
4. DevPulse opaque sessions persisted in PostgreSQL, with more than one concurrent session allowed per user
5. Session restoration, expiration and revocation
6. Protected backend APIs (enforced server-side)
7. Protected frontend routes
8. A separate Profile section
9. Profile metadata refresh, performed by sending the user through GitHub authorization again [REV1]
10. GitHub App installation on the user's **personal** GitHub account [REV1]; an installation callback that reports an organisation account is rejected [REV2]
11. All-repositories authorization
12. Selected-repositories authorization
13. Installation verification before an installation is marked active
14. Installation metadata persistence
15. Tool Configuration metadata persistence (as part of the connection's data) [REV1]
16. Connection-status display
17. Permission-status display
18. Verification of the connection with GitHub when Tool Configuration is opened, and on request [REV1]
19. Logout
20. GitHub disconnection that does **not** log the user out, and reconnection, including reactivation of the user's own disconnected installation [REV2]
21. Secure credential-handling requirements
22. BDD acceptance behaviour

## 3. Goals

- G1. A visitor can sign in with GitHub and is recognised again after a browser refresh.
- G2. Each GitHub person maps to exactly one DevPulse user, whatever happens to their username, name, avatar or email.
- G3. An authenticated user can install the DevPulse GitHub App on their personal account, see the verified connection and its permission status, and disconnect it.
- G4. Authentication and GitHub repository authorization stay separate, observable states.
- G5. No credential is ever exposed to the browser's readable storage, to URLs, to logs or to user-visible errors.
- G6. Phase 2 leaves a verified, user-owned connection that Phase 3 can build on, without implementing Phase 3.

## 4. Non-goals (explicit; must not be implemented, stubbed or exposed in the UI)

- Commits, pull requests, pull-request reviews, issues
- Repository language retrieval and technology detection
- Workflows and workflow-run retrieval
- Repository analytics, dashboard widgets, dashboard charts
- Celery, Redis, Celery Beat, background jobs, scheduled synchronization
- Manual repository-data synchronization and any synchronization control in the UI
- GitHub webhooks and repository reconciliation. Changes made on GitHub are discovered only when DevPulse verifies the connection (FR-CONF-006, FR-CONF-005). [REV1]
- Repository source-code storage
- GitLab and Bitbucket
- Email-and-password authentication
- Repository discovery and repository selection inside DevPulse (Phase 3). Phase 2 only reflects whether GitHub grants all or selected repositories.
- **Organisation installations.** Phase 2 supports personal GitHub accounts only. [REV1]

Where the UI must hint at later phases, only a neutral placeholder is allowed (for example, "Not yet synchronized"). Scenario `Phase 2 performs no repository-activity synchronization` in `phase-02-acceptance.feature.md` proves this non-goal.

## 5. Actors

| Actor | Description |
|---|---|
| Visitor | Not signed in to DevPulse; has no connection state |
| Signed-in user | Holds a valid DevPulse session; the owner of their own profile and connection |
| Another signed-in user | Used in ownership and isolation scenarios; must never see or change the first user's data |
| GitHub | External identity and installation authority; may be slow, unavailable, rate-limiting, or may report suspension, removal or changed permissions when DevPulse verifies the connection |

## 6. User journeys

- **J1 First-time user.** Visitor chooses Continue with GitHub, authorizes on GitHub, becomes a signed-in user (Authentication completed), installs the GitHub App on their personal account (all or selected repositories), and sees a verified Connected state. After the user starts installation, the state stays Installation required until installation completes. [REV2]
- **J2 Returning user.** Visitor signs in again, DevPulse recognises the same user, updates changed profile data, and the previous connection is shown unchanged.
- **J3 Signed in, not installed.** User is signed in and sees Authentication completed, with the option to install and no repository access.
- **J4 No email or no display name from GitHub.** Authentication still succeeds; the Profile shows "Email not available from GitHub" and "Name not provided by GitHub" as applicable.
- **J5 Profile refresh.** User chooses Refresh, is taken to GitHub, returns, and sees updated data and a new refresh time; if the user cancels or GitHub denies, the stored profile is unchanged and a safe message is shown. [REV1]
- **J6 Logout.** User logs out. Only that session ends. The GitHub installation stays.
- **J7 Disconnect.** User confirms disconnection. Repository access is disabled first, then DevPulse asks GitHub to remove the installation. The user stays signed in.
- **J8 External change.** GitHub suspends or removes the installation, or changes its permissions. DevPulse shows the matching state when it next verifies the connection (on opening Tool Configuration or on request). [REV1]
- **J9 Reconnect.** After disconnection or deletion, the user reconnects through a new installation. If the installation ID is new, the earlier record stays as history; if it is the user's own disconnected installation ID, the existing record is reactivated after verification. [REV2]

## 7. Functional requirements

### 7.1 Authentication (AUTH)

| ID | Priority | Source | Requirement |
|---|---|---|---|
| FR-AUTH-001 | Must | Intent; PRD FR-AUTH-001 | DevPulse must allow a visitor to start GitHub authorization from a "Continue with GitHub" action. |
| FR-AUTH-002 | Must | Intent; PRD FR-AUTH-002 | After successful GitHub authorization, DevPulse must create a local user, or update the existing local user, identified solely by the stable GitHub user ID. |
| FR-AUTH-003 | Must | Intent; PRD FR-AUTH-002 | When the authorized GitHub username, display name, avatar or email differs from the stored values, DevPulse must update the existing user and must not create a duplicate user. |
| FR-AUTH-004 | Must | Handoff | DevPulse must complete authentication, user creation and session creation when GitHub provides no email. |
| FR-AUTH-005 | Must | Intent | DevPulse must record the time of each successful authentication as the user's last login time. |
| FR-AUTH-006 | Must | [REV1] Revision 1, B7 | When two first sign-ins for the same GitHub account happen at the same time, DevPulse must end with exactly one local user for that account and must sign in both requests as that user. |

### 7.2 Session (SESS)

| ID | Priority | Source | Requirement |
|---|---|---|---|
| FR-SESS-001 | Must | Intent; PRD FR-AUTH-003 | After successful authentication, DevPulse must create a server-controlled session and deliver its credential to the browser in an HTTP-only cookie. |
| FR-SESS-002 | Must | Intent; PRD FR-AUTH-004 | DevPulse must recognise a valid session after a browser refresh without asking the user to authenticate again. |
| FR-SESS-003 | Must | Handoff | DevPulse must let the signed-in interface retrieve the current user's identity and profile summary using the session alone. |
| FR-SESS-004 | Must | Intent; PRD FR-AUTH-006 | A signed-in user must be able to log out, and logging out must revoke the current DevPulse session. |
| FR-SESS-005 | Must | Handoff | Logging out when the session is already revoked, expired or absent must complete without error and leave the user unauthenticated. |
| FR-SESS-006 | Must | Handoff | DevPulse must never accept an expired session. The lifetime values are an open decision (OQ-001). |
| FR-SESS-007 | Could | Handoff | DevPulse should remove or retire expired and revoked sessions over time. The strategy is an open decision (OQ-004). |
| FR-SESS-008 | Must | [REV1] Decision A10 | DevPulse must allow the same user to hold more than one session at the same time, and logging out must end only the session used for the logout request. |

### 7.3 Profile (PROF)

| ID | Priority | Source | Requirement |
|---|---|---|---|
| FR-PROF-001 | Must | Intent | DevPulse must retrieve and store the authorized GitHub profile metadata for the user when they authenticate. |
| FR-PROF-002 | Must | Intent | The Profile section must show the user's name, avatar, username, email when available, GitHub profile link, account type, DevPulse account creation time, last login time and last profile refresh time. |
| FR-PROF-003 | Must | Handoff | When no email is available from GitHub, the Profile must show the text "Email not available from GitHub" and DevPulse must not display an invented email. |
| FR-PROF-004 | Must | [REV1] Intent; Decision A2 | A signed-in user must be able to request a profile refresh. DevPulse must take the user through GitHub authorization again, and on the user's return must show the refreshed profile. |
| FR-PROF-005 | Must | [REV1] Intent; Decision A2 | On a successful refresh, DevPulse must update the changed metadata and the last profile refresh time, must keep the same user identity, and must show the user a confirmation and the new last profile refresh time. |
| FR-PROF-006 | Must | [REV1] Decision A11 | When GitHub provides no display name, the Profile must show the text "Name not provided by GitHub" and must not show the username in its place. |
| FR-PROF-007 | Must | [REV1] Decision A9 | DevPulse must store the account's primary verified email when GitHub makes it available under the granted authorization; otherwise the public email if available; otherwise no email. |

### 7.4 Access control (ACC)

| ID | Priority | Source | Requirement |
|---|---|---|---|
| FR-ACC-001 | Must | PRD FR-AUTH-005 | Protected backend interfaces must reject unauthenticated requests, independently of any frontend route protection. |
| FR-ACC-002 | Must | PRD FR-AUTH-005 | Protected frontend routes must send an unauthenticated visitor to sign-in instead of showing protected content. |
| FR-ACC-003 | Should | [INFERRED] | After sign-in, DevPulse should return the user to the in-application route they originally requested. |

### 7.5 GitHub App installation (INST)

| ID | Priority | Source | Requirement |
|---|---|---|---|
| FR-INST-001 | Must | Intent; PRD FR-GH-001 | A signed-in user must be able to start installation of the DevPulse GitHub App. |
| FR-INST-002 | Must | PRD FR-GH-002 | DevPulse must support an installation that grants access to all repositories and an installation that grants access to selected repositories, and must show which mode applies. |
| FR-INST-003 | Must | [REV1] Intent; Decision A5 | DevPulse must support installation on the user's personal GitHub account. Phase 2 supports personal accounts only. |
| FR-INST-004 | Retired | [REV1] Decision A5 | RETIRED (organisation installations are a Phase 2 non-goal, revision 1). Original text: DevPulse could support installation on a GitHub organisation account. |
| FR-INST-005 | Must | Handoff | DevPulse must verify an installation with GitHub before marking it active. |
| FR-INST-006 | Must | PRD FR-GH-003 | DevPulse must associate a verified installation with the signed-in user who started the installation. |
| FR-INST-007 | Must | Handoff | Receiving the same installation callback more than once must not create duplicate records and must leave a single installation record. |
| FR-INST-008 | Must | [REV1] [REV2] Intent; Decision A8; Decision R2-2a; Decision R2-9 | A user whose connection is Connected, Permission attention required, Suspended or Verification failed must be able to open GitHub's page for managing the installation. This wording does not claim that the installation is known to exist in the Verification failed state. |
| FR-INST-009 | Must | [REV1] [INFERRED] | While the state is Authentication completed or Installation required, DevPulse must let the user start, or restart, installation of the DevPulse GitHub App. |
| FR-INST-010 | Must | [REV2] Decision R2-10 | When a reconnect returns the installation ID of the user's own Disconnected connection, DevPulse must, after verification, reactivate that existing record as the user's current connection and update it. Exactly one record must exist for that installation ID, the user must have at most one current connection, and the earlier period must not be kept as a separate record in this case. |

### 7.6 Tool Configuration (CONF)

| ID | Priority | Source | Requirement |
|---|---|---|---|
| FR-CONF-001 | Must | Intent | DevPulse must provide a Tool Configuration area that presents GitHub as a configurable provider with its current configuration state. |
| FR-CONF-002 | Must | Intent; phase prompt s7 | When a connection exists, Tool Configuration must show: provider name, connected GitHub user, installation account and account type, DevPulse authentication status, GitHub installation status, repository-authorization mode, authorized repository count when available, permission status, configuration status and last verification time. |
| FR-CONF-003 | Must | Intent | DevPulse must keep the user's Tool Configuration across logout and login. |
| FR-CONF-004 | Must | [REV1] Intent; Revision 1, B4 | Tool Configuration must offer, for the current connection state, exactly the actions listed for that state in section 13, and no other action. |
| FR-CONF-005 | Must | [REV1] [REV2] Decision A3; Decision R2-2; Decision R2-9 | A signed-in user whose connection is Connected, Permission attention required, Suspended or Verification failed must be able to request re-verification of it. In the Verification failed state the action must be labelled "Retry verification". |
| FR-CONF-006 | Must | [REV1] Decision A3 | DevPulse must verify the connection with GitHub when the user opens Tool Configuration. |

### 7.7 Connection status (STAT)

| ID | Priority | Source | Requirement |
|---|---|---|---|
| FR-STAT-001 | Must | [REV1] Intent; PRD FR-GH-005; Decision A4 | DevPulse must represent exactly one of these eight connection states for a signed-in user at any time: Authentication completed, Installation required, Connected, Permission attention required, Suspended, Installation deleted, Verification failed, Disconnected. A visitor who is not signed in has no connection state. |
| FR-STAT-002 | Must | Handoff | DevPulse must present DevPulse authentication status and GitHub installation status as separate indicators. |
| FR-STAT-003 | Must | [REV1] Intent; Decision A7 | DevPulse must show the permission status of a connection by comparing the permissions granted to the installation with the permissions required by SR-PERM-001. |
| FR-STAT-004 | Retired | [REV1] Decision A4 | RETIRED (the Not configured state was merged into Authentication completed, revision 1). Original text: DevPulse must show Not configured for a visitor who is not authenticated and has no installation. |
| FR-STAT-005 | Must | [REV1] [REV2] Handoff; Decision A4; Decision R2-1 | DevPulse must show Authentication completed for a signed-in user who has no current connection and has never started installation or reconnection, and must treat repository access as unavailable. |
| FR-STAT-006 | Must | [REV1] [REV2] Decision R2-1 | DevPulse must show Installation required from the moment the user starts installation, or starts reconnection, until installation completes. Cancelling at GitHub does not change the state. The state has no expiry and never returns to Authentication completed by itself. Repository access is unavailable. |
| FR-STAT-007 | Must | [REV2] Handoff; Decision R2-3 | DevPulse must show Connected for a verified installation that is active and has the required permissions. Repository access is available in this state (BR-002). |
| FR-STAT-008 | Must | [REV1] [REV2] Handoff; Decision A3; Decision R2-3 | When DevPulse verifies the connection and finds that the granted permissions do not match the required permissions, DevPulse must show Permission attention required and must identify the permissions affected. |
| FR-STAT-009 | Must | [REV1] Handoff; PRD FR-GH-005; Decision A3 | When DevPulse verifies the connection and GitHub reports the installation as suspended, DevPulse must show Suspended and must treat repository access as unavailable. |
| FR-STAT-010 | Must | [REV1] Handoff; Decision A3 | When DevPulse verifies the connection and GitHub reports that the installation no longer exists, DevPulse must show Installation deleted and must treat repository access as unavailable. |
| FR-STAT-011 | Must | [REV1] Handoff; PRD FR-GH-005; Decision A3 | When DevPulse verifies the connection and cannot confirm the installation for a reason other than a temporary failure, DevPulse must show Verification failed, must treat repository access as unavailable, and must always offer Retry verification. |
| FR-STAT-012 | Must | Handoff; PRD FR-GH-005 | DevPulse must show Disconnected after the user disconnects GitHub, and must treat repository access as unavailable. |
| FR-STAT-013 | Retired | [REV1] [REV2] Decision R2-1 | RETIRED (Installation required does not expire, revision 2). Original text: When an installation attempt expires without completion, DevPulse must return the connection state to Authentication completed. The attempt lifetime is a design-stage parameter linked to OQ-012. |

### 7.8 Disconnection (DISC)

| ID | Priority | Source | Requirement |
|---|---|---|---|
| FR-DISC-001 | Must | [REV2] Intent; PRD FR-GH-006; Decision R2-2 | A user whose connection is Connected, Permission attention required, Suspended or Verification failed must be able to request disconnection of GitHub. |
| FR-DISC-002 | Must | [INFERRED] | DevPulse must ask the user to confirm disconnection, and cancelling must leave the connection unchanged. |
| FR-DISC-003 | Must | [REV1] Handoff; Decision A8 | On confirmed disconnection, DevPulse must first disable repository access locally, set the state to Disconnected and record the disconnection time, and only then ask GitHub to remove the installation. |
| FR-DISC-004 | Must | Handoff | Requesting disconnection of an already disconnected connection must complete safely with no change and no error. |
| FR-DISC-005 | Must | [REV1] [REV2] Handoff; Decision A8; Decision R2-9 | A user whose connection is Disconnected or Installation deleted must be able to reconnect. Reconnecting must start a new installation and, when the new installation has a different installation ID, keep the earlier connection on record as history. FR-INST-010 covers the case where the installation ID is the user's own. |
| FR-DISC-006 | Must | [REV1] Decision A8 | DevPulse must not offer reconnection for a Suspended installation. It must offer Manage installation on GitHub instead. |

## 8. Security requirements

| ID | Priority | Source | Requirement |
|---|---|---|---|
| SR-CRED-001 | Must | Handoff s3.2 | The DevPulse session credential must be random, high-entropy and opaque, and only a cryptographic hash of it may be persisted. The raw value must never be stored in PostgreSQL. |
| SR-CRED-002 | Must | Handoff s3.2 | The GitHub App private key must never be stored in normal PostgreSQL application tables, and must never be committed, returned to React, logged or shown in errors. Production must hold it in a managed secret store; local development must hold it in a protected environment-mounted secret. |
| SR-CRED-003 | Must | Handoff s3.2 | GitHub installation access tokens must be short-lived, generated only when an approved GitHub operation needs one, and not treated as permanent credentials. They should not be persisted. |
| SR-CRED-004 | Must | [REV1] Handoff s3.2; Decision A2 | Tokens obtained during GitHub user authorization may be used only for the authorization or profile retrieval in progress and must not be persisted. Persisting them in a later phase requires a new explicit approval. |
| SR-CRED-005 | Must | Handoff s6; PRD NFR-SEC-001 | Credentials must not appear in browser local storage, browser session storage, JavaScript-readable cookies, persistent React state, URLs, query parameters, frontend API responses, user-visible errors or real test fixtures. |
| SR-CRED-006 | Must | PRD NFR-SEC-001 | Credentials, authorization headers and cookies must be redacted from logs. When background jobs are introduced in a later phase, credentials must not be passed in job arguments; this part is a forward-looking constraint and is not exercised in Phase 2. |
| SR-SESS-001 | Must | Handoff | DevPulse must issue a new session credential at every successful authentication and must not honour any credential presented before authentication (session-fixation prevention). |
| SR-SESS-002 | Must | Handoff; PRD NFR-SEC-002 | The session cookie must be HTTP-only; in production it must also be Secure and use an approved SameSite policy (OQ-003) and be time-limited. |
| SR-STATE-001 | Must | [REV1] PRD NFR-SEC-003; Decision A2 | Every authorization callback, for sign-in and for profile refresh, must be accepted only with a short-lived, single-use, correlated state value; a missing, invalid, expired, reused or mismatched value must be rejected (replay protection). |
| SR-STATE-002 | Must | PRD NFR-SEC-003 | The installation callback must be accepted only when it can be correlated to an installation that the signed-in user started. |
| SR-CSRF-001 | Must | [REV1] Phase prompt s8; Revision 1, B6 | State-changing requests that rely on the session cookie must be protected against cross-site request forgery. This applies at least to logout, disconnection, starting installation, starting a profile refresh and requesting re-verification. The approach is an open decision (OQ-013) and must assume the frontend and backend are served from the same site (OQ-022). |
| SR-AUTHZ-001 | Must | PRD NFR-SEC-005 | Every user-scoped read and change (profile, connection, configuration, status, disconnection) must be limited to its owner on the server, and cross-user access must be denied. |
| SR-PERM-001 | Must | [REV1] PRD FR-GH-007; Decision A7 | The GitHub App must request only the minimum permissions Phase 2 needs. It must request no repository-content permission, no repository-activity permission and no write permission. Read access to the user's email address is part of the Phase 2 minimum; the design stage must verify what GitHub requires for it. Any increase requires explicit owner approval. |
| SR-REDIR-001 | Must | Handoff; frontend instructions | A post-login destination must be limited to known in-application routes. An arbitrary or external destination must never be followed. |
| SR-ERR-001 | Must | Backend and frontend instructions | User-visible errors must be safe and actionable, and must not contain stack traces, raw GitHub error content, tokens or internal data details. |
| SR-PRIV-001 | Could | [INFERRED] | DevPulse should store only the profile attributes listed in DR-USER-002 and must not store GitHub attributes it does not need. |

## 9. Data requirements

Requirements describe what is kept, not how. Table names, columns and schemas belong to the design stage.

| ID | Priority | Source | Requirement |
|---|---|---|---|
| DR-USER-001 | Must | Intent | DevPulse must keep at most one local user per stable GitHub user ID. |
| DR-USER-002 | Must | Intent | DevPulse must keep, for each user: stable GitHub user ID, username, display name when available, avatar address, authorized email when available, GitHub profile address, account type, DevPulse account creation time, last login time and last profile refresh time. |
| DR-USER-003 | Must | Backend instructions | DevPulse must store all times as timezone-aware UTC values. |
| DR-SESS-001 | Must | Handoff | DevPulse must keep, for each session: the owning user, a hash of the credential, creation time, expiry time and revocation status. |
| DR-STATE-001 | Must | PRD NFR-SEC-003 | DevPulse must keep authorization and installation correlation values with an expiry and a consumed marker so each value works once. |
| DR-CONN-001 | Must | [REV1] Phase prompt s7; Decision A8 | DevPulse must keep, for each connection: internal connection ID, owning DevPulse user, provider, GitHub installation ID, installation account ID, account login, account type, repository-selection mode, granted-permission metadata, installation status, connection status, installation creation time when available, local creation and update times, last verification time, suspension time when applicable, disconnection time when applicable and a removal-pending marker. |
| DR-CONN-002 | Must | Handoff; PRD FR-GH-004 | A GitHub installation ID must be unique across all DevPulse users. |
| DR-CONN-003 | Must | PRD FR-GH-003 | Each connection must belong to exactly one DevPulse user. |
| DR-CONN-004 | Must | Handoff | A disconnected connection must remain on record with its disconnection time. |
| DR-CONN-005 | Must | [REV1] [REV2] Decision A6; Decision R2-10 | A user must have at most one current connection. Earlier Disconnected or Installation deleted connections must remain on record as history, except when a reconnect returns the user's own installation ID and the existing record is reactivated (FR-INST-010). |
| DR-CONN-006 | Must | [REV1] Decision A5 | DevPulse must be able to store an account-type value other than "User" for the user and for the installation account, without treating it as an error. |
| DR-CONF-001 | Must | [REV1] Intent; Revision 1, B5 | Tool Configuration metadata (the provider, the configuration status and the last verification time) is part of the connection's data and not a separate duplicated set. It must persist across logout, login and browser restarts. |

## 10. User interface requirements

| ID | Priority | Source | Requirement |
|---|---|---|---|
| UI-AUTH-001 | Must | Handoff | The sign-in page must offer GitHub as the only way to sign in and must not show email or password fields. |
| UI-AUTH-002 | Must | Frontend instructions | When authentication fails, the sign-in page must show a safe message that says what happened and offer a retry. |
| UI-PROF-001 | Must | Intent | The Profile must be a section of its own, separate from Tool Configuration, and reachable from authenticated navigation. |
| UI-PROF-002 | Could | Handoff s5 | Where the Profile hints at later phases, it may show only the neutral placeholder "Not yet synchronized". |
| UI-CONF-001 | Must | Handoff s7 | Tool Configuration must show no synchronization controls and no synchronization status. |
| UI-CONF-002 | Must | Figma foundations; frontend instructions | Every status must be conveyed with text, not by colour alone. |
| UI-STATE-001 | Must | Frontend instructions | Pages in this phase must provide loading, success, recoverable-error and backend-unavailable states. |
| UI-NAV-001 | Should | [INFERRED] | Authenticated navigation items (Profile, Tool Configuration, logout) must not be offered to a visitor. |
| UI-A11Y-001 | Must | PRD UX-004 | Every control in these pages must be reachable and operable by keyboard, have visible focus and an accessible name, and meet WCAG 2.2 AA contrast. |
| UI-TIME-001 | Must | [REV1] [REV2] Decision A13c; Decision R2-7 | Every time shown to the user must be displayed in UTC, labelled as UTC, and in exactly the form of the example "16 Nov 2026, 09:26 UTC". Details the example does not settle are not decided here (OQ-026). |

## 11. Business rules

| ID | Priority | Source | Rule |
|---|---|---|---|
| BR-001 | Must | Handoff | The stable GitHub user ID is the only identity key. Username, display name and email must never identify a user. |
| BR-002 | Must | [REV1] [REV2] Revision 1, B1; Decision R2-3 | Repository access is available when the user is authenticated and the connection state is Connected. It is unavailable in Authentication completed, Installation required, Suspended, Installation deleted, Verification failed and Disconnected. Its availability in Permission attention required is not specified in Phase 2 (OQ-025). |
| BR-003 | Must | Handoff | Logging out must not change or remove the GitHub App installation. |
| BR-004 | Must | Handoff | Disconnecting GitHub must not end the DevPulse session. |
| BR-005 | Must | Handoff; PRD FR-GH-004 | A GitHub installation ID belongs to at most one DevPulse user and must never be silently reassigned to another user. |
| BR-006 | Must | Phase prompt s5 | Phase 2 must not retrieve or store repository activity of any kind. |
| BR-007 | Must | Product context | DevPulse must use neutral, evidence-based language and must not present profile or connection data as a measure of productivity or skill. |
| BR-008 | Must | Handoff | DevPulse must never invent an email for a user. |

## 12. Error conditions

| ID | Priority | Source | Condition and required behaviour |
|---|---|---|---|
| ER-AUTH-001 | Must | Phase prompt s9.2 | When the user cancels at GitHub, DevPulse must create no session, leave the visitor unauthenticated, and offer a safe way to try again. |
| ER-AUTH-002 | Must | Phase prompt s9.2 | When GitHub denies authorization, DevPulse must create no session and must show a safe explanation. |
| ER-AUTH-003 | Must | Phase prompt s9.2 | When the authorization callback has no authorization code, DevPulse must reject it and create no session. |
| ER-AUTH-004 | Must | Phase prompt s9.2 | When the authorization callback has no state value, DevPulse must reject it and create no session. |
| ER-AUTH-005 | Must | Phase prompt s9.2 | When the state value is unknown to DevPulse, DevPulse must reject the callback and create no session. |
| ER-AUTH-006 | Must | Phase prompt s9.2 | When the state value has expired, DevPulse must reject the callback and create no session. |
| ER-AUTH-007 | Must | Phase prompt s9.2 | When the state value was already used, DevPulse must reject the callback and create no session. |
| ER-AUTH-008 | Must | Phase prompt s9.2 | When the state value does not belong to the browser that started authorization, DevPulse must reject the callback and create no session. |
| ER-AUTH-009 | Must | Phase prompt s9.2 | When GitHub is temporarily unavailable during authentication, DevPulse must create no session, show a retryable message and leave existing users unchanged. |
| ER-SESS-001 | Must | Phase prompt s9.2 | A request with no session must be treated as unauthenticated. |
| ER-SESS-002 | Must | Phase prompt s9.2 | A request with an unrecognised or malformed session credential must be treated as unauthenticated. |
| ER-SESS-003 | Must | Phase prompt s9.2 | A request with an expired session must be treated as unauthenticated. |
| ER-SESS-004 | Must | Phase prompt s9.2 | A request with a revoked session must be treated as unauthenticated. |
| ER-ACC-001 | Must | PRD FR-AUTH-005 | A protected backend request without a valid session must receive an authentication-required response that exposes no protected data and does not reveal whether a session ever existed. |
| ER-INST-001 | Must | Handoff | An installation callback with no valid DevPulse session must not be associated with any user. |
| ER-INST-002 | Must | Phase prompt s9.2 | An installation callback with no installation ID must be rejected and must create no installation record. |
| ER-INST-003 | Must | Phase prompt s9.2 | An installation callback that cannot be correlated to an installation the user started must be rejected and must create no installation record. |
| ER-INST-004 | Must | [REV2] Handoff; Decision R2-11 | An installation callback for an installation ID that belongs to another user, whether that user's record is current or Disconnected, must be rejected. DevPulse must leave that record untouched, must not reassign the installation, and must tell the signed-in user safely. |
| ER-INST-005 | Must | Handoff | When verification does not confirm the installation, DevPulse must not mark it active and must show Verification failed. |
| ER-INST-006 | Must | [REV1] [REV2] Phase prompt s9.2; Decision R2-1 | When the user cancels installation at GitHub, DevPulse must create no connection, keep the user signed in and keep showing Installation required. Cancelling does not change the state. |
| ER-INST-007 | Must | [INFERRED] | When GitHub is temporarily unavailable during verification of an installation callback, DevPulse must not mark the installation active and must show a retryable message. |
| ER-INST-008 | Must | [REV2] Decision R2-12; consequence [INFERRED] | An installation callback that reports an organisation account must be rejected with a safe message that only personal GitHub accounts are supported in Phase 2, and no connection must be created. `[INFERRED]` consequence: because the installation is not completed, the state remains as it was before the callback (Installation required). |
| ER-PROF-001 | Must | [REV1] Phase prompt s9.2; Decision A2 | When the user cancels at GitHub, or GitHub denies authorization, during a profile refresh, DevPulse must leave the stored profile unchanged and show a safe message. |
| ER-PROF-002 | Must | [REV1] Phase prompt s9.2; Decision A2 | When a profile refresh fails temporarily because GitHub is unavailable, DevPulse must keep the stored profile, show when it was last refreshed and offer a retry. |
| ER-PROF-003 | Must | [REV1] [REV2] Decision R2-4 | When the GitHub account that authorizes a profile refresh is not the signed-in user's GitHub account, DevPulse must reject the refresh, leave the stored profile unchanged and show a safe message. |
| ER-DISC-001 | Must | [REV1] Phase prompt s8; Decision A8 | When GitHub fails to remove the installation after disconnection, the connection must stay Disconnected and be marked removal pending, and DevPulse must show the user safe instructions to remove the App on GitHub. No credential or raw GitHub error may be shown. |
| ER-DISC-002 | Must | Phase prompt s9.2 | When the installation is already removed at GitHub, disconnection must still complete and leave the connection Disconnected. |
| ER-CONF-001 | Must | [REV1] [REV2] Decision A3; Decision R2-6 | When GitHub is temporarily unavailable while DevPulse verifies an existing connection, DevPulse must keep showing the last known state, its last verification time and a retry option, and must show a visible notice that the connection could not be verified now. |
| ER-SYS-001 | Must | Frontend instructions | When the backend is unavailable, the interface must show a safe unavailable state and must not show stale protected content as current. |
| ER-SYS-002 | Should | [INFERRED] | When GitHub rate-limits authentication, verification or refresh, DevPulse must show a safe retry-later message and must not change stored state. |

## 13. Connection states

DevPulse learns of GitHub-side changes only when it verifies the connection (FR-CONF-006 on opening Tool Configuration, FR-CONF-005 on request). It never learns of them by notification from GitHub. Repository access is available in Connected (BR-002) and unavailable in every state except Permission attention required, whose repository access is not specified in Phase 2 (OQ-025). Every state below has at least one Must action and at least one exit. Tool Configuration shows no synchronization controls in any state (UI-CONF-001), and offers exactly the actions listed (FR-CONF-004).

| State | How the user enters it | Tool Configuration shows | Repository access | Actions offered | How it exits |
|---|---|---|---|---|---|
| Authentication completed | Signed in with no current connection, and installation or reconnection never started (FR-STAT-005) | GitHub user, DevPulse authentication: signed in, GitHub installation: not installed | Unavailable | Install the DevPulse GitHub App (FR-INST-001) | User starts installation, then Installation required |
| Installation required | User starts installation, or starts reconnection; stays until installation completes. Cancelling at GitHub does not change the state. No expiry (FR-STAT-006) | Installation-required message | Unavailable | Install the DevPulse GitHub App, to restart (FR-INST-009) | Verified callback, then Connected; callback not confirmed, then Verification failed. It never returns to Authentication completed by itself |
| Connected | Verified callback (FR-INST-005); or a later verification confirms the installation, with the required permissions, after Permission attention required, Suspended or Verification failed | All fields in FR-CONF-002 | Available | Manage installation (FR-INST-008), Re-verify (FR-CONF-005), Disconnect (FR-DISC-001) | A later verification finds permissions differ, then Permission attention required; reports suspended, then Suspended; reports removed, then Installation deleted; cannot confirm, then Verification failed; user disconnects, then Disconnected |
| Permission attention required | Verification finds the granted permissions differ from the required permissions (FR-STAT-008) | Connection details and the permissions that need attention | Not specified in Phase 2 (OQ-025) | Manage installation, Re-verify, Disconnect | Permissions restored and a verification confirms, then Connected; other verification outcomes lead to the matching state; user disconnects, then Disconnected |
| Suspended | Verification reports the installation as suspended (FR-STAT-009) | Suspended notice | Unavailable | Manage installation, Re-verify, Disconnect. Reconnect is not offered (FR-DISC-006) | GitHub unsuspends and a verification confirms, then Connected; other verification outcomes lead to the matching state; user disconnects, then Disconnected |
| Installation deleted | Verification reports the installation no longer exists (FR-STAT-010) | Removed-at-GitHub notice | Unavailable | Reconnect (FR-DISC-005) | User reconnects, then Installation required; the old record stays as history |
| Verification failed | An installation callback is not confirmed (ER-INST-005), or verification of an existing connection cannot confirm it for a reason that is not temporary (FR-STAT-011) | Safe failure message | Unavailable | Retry verification (FR-STAT-011, FR-CONF-005), Manage installation (FR-INST-008), Disconnect (FR-DISC-001) | A successful retry leads to the state GitHub reports, normally Connected; user disconnects, then Disconnected |
| Disconnected | User completes disconnection (FR-DISC-003) | Disconnected notice with the disconnection time; if removal is pending, safe instructions to remove the App on GitHub (ER-DISC-001) | Unavailable | Reconnect (FR-DISC-005) | User reconnects, then Installation required; the old record stays as history |

When GitHub is temporarily unavailable during verification, the state does not change; DevPulse shows the last known state, its last verification time, a retry option and a notice that the connection could not be verified now (ER-CONF-001). When an installation callback is rejected because it reports an organisation account, no connection is created and the state remains as it was before the callback, which is Installation required (ER-INST-008; the consequence is `[INFERRED]`).

## 14. Assumptions (summary; details in `assumptions.md`)

Twenty-three assumptions are recorded. Revision 0 and 1 resolved A-001, A-004 to A-008, A-012 to A-014 and updated A-009 and A-010. Revision 2 resolves A-016 to A-022 by owner decisions R2-1 to R2-8 and adds one inferred assumption, A-023 (`[REV2]` `[INFERRED]`): after a rejected organisation callback the state remains Installation required.

## 15. Open decisions (summary; details in `open-questions.md`)

Twenty-eight open questions are recorded. Fifteen are DECIDED by the owner (OQ-002, 006, 007, 008, 009, 010, 011, 014, 015, 016, 018, 019, 021, 022, 023). Thirteen remain open for the design stage: session lifetime and expiry model (OQ-001), SameSite and cookie name (OQ-003), session cleanup (OQ-004), one GitHub App or two (OQ-005), authorization state lifetime and storage (OQ-012), CSRF approach (OQ-013), installation callback correlation (OQ-017), account-type handling (OQ-020), the expired installation correlation value while Installation required (OQ-024, new), repository access in Permission attention required, to be answered in Phase 3 (OQ-025, new), time-display details (OQ-026, new), clearing the removal-pending marker (OQ-027, new) and the text of the GitHub installation indicator per state (OQ-028, new).

## 16. Acceptance criteria

Phase 2 requirements are accepted when:

1. Every scenario in `features/*.feature.md` is agreed by the product owner as the observable behaviour.
2. Every active requirement in sections 7 to 12 is covered by at least one scenario (`requirements-bdd-coverage.md`), every retired requirement is marked Retired, and every Partial item is linked to an open question with a specific explanation.
3. The journeys J1 to J9 are demonstrable end to end.
4. All credential-handling rules in SR-CRED-001 to SR-CRED-006 are verifiable.
5. `phase-02-acceptance.feature.md` proves that no repository activity is synchronized.
6. The Phase 1 completion step (P-1) has been approved before implementation starts.
7. Scenarios blocked by an open question are tightened once that question is decided. [REV2]

## 17. Definition of Done (for the later implementation, per PRD section 25)

- Approved requirements are implemented.
- Requirement, BDD, test and code traceability is updated.
- Automated tests pass, including regression.
- Security requirements are verified: tokens absent from logs, responses and browser-readable storage; raw session credentials not persisted; cookie attributes; state replay rejected; cross-user access denied; duplicate callbacks create no duplicates.
- Database schema changes use Alembic migrations that apply and, where feasible, roll back.
- Loading, success, empty, error and backend-unavailable states are covered.
- Documentation is updated.
- No implementation deviates from the approved design without recorded approval.
- The product owner approves the phase result.
