# Phase 2: Open Questions

Each question keeps its original options, trade-offs and recommendation for the record. A question is either **DECIDED by owner, 2026-11-24** (the decision text is authoritative and the earlier recommendation is history) or **OPEN** (a design-stage question; nothing here is decided). Anything new in revision 1 carries `[REV1]`; anything new or changed in revision 2 carries `[REV2]`. GitHub behaviours mentioned have not been verified against GitHub documentation (assumption A-011).

## Index

| ID | Topic | Status |
|---|---|---|
| OQ-001 | Session lifetime and expiry model | OPEN |
| OQ-002 | Concurrent sessions per user | DECIDED |
| OQ-003 | SameSite policy and cookie name | OPEN |
| OQ-004 | Session cleanup strategy | OPEN |
| OQ-005 | One GitHub App or an OAuth App plus a GitHub App | OPEN |
| OQ-006 | Persisting GitHub user access and refresh tokens | DECIDED |
| OQ-007 | Organisation installations in Phase 2 | DECIDED |
| OQ-008 | Reconnect after external deletion or suspension | DECIDED |
| OQ-009 | Failure to remove the installation during disconnection | DECIDED |
| OQ-010 | GitHub App permissions requested | DECIDED |
| OQ-011 | Disconnection: uninstall at GitHub or disable locally only | DECIDED |
| OQ-012 | Authorization state lifetime and storage | OPEN |
| OQ-013 | CSRF protection approach | OPEN |
| OQ-014 | Detecting GitHub-side changes before webhooks exist | DECIDED |
| OQ-015 | Definitions of the early states | DECIDED |
| OQ-016 | Multiple installations per user | DECIDED |
| OQ-017 | Correlating the installation callback to the user who started it | OPEN |
| OQ-018 | Authorization used for profile refresh | DECIDED |
| OQ-019 | Which email DevPulse accepts | DECIDED |
| OQ-020 | Account-type values | OPEN |
| OQ-021 `[REV1]` | Installation ID that matches a disconnected record | DECIDED (marker question moved to OQ-027) |
| OQ-022 `[REV1]` | Deployment topology of frontend and backend | DECIDED |
| OQ-023 `[REV1]` | Behaviour when an installation callback reports an organisation account | DECIDED |
| OQ-024 `[REV2]` | Installation correlation value expired while Installation required | OPEN |
| OQ-025 `[REV2]` | Repository access in Permission attention required (answered in Phase 3) | OPEN |
| OQ-026 `[REV2]` | Time-display details not settled by the example | OPEN |
| OQ-027 `[REV2]` | How the removal-pending marker is cleared | OPEN |
| OQ-028 `[REV2]` | Text of the GitHub installation indicator per state | OPEN |

---

## OQ-001 Session lifetime and expiry model
- **Status:** OPEN (design stage).
- **Why it matters:** sets how long a stolen or forgotten session stays usable versus how often users sign in again.
- **Options:** (A) fixed absolute lifetime, e.g. 7 days; (B) idle timeout that slides on use, plus an absolute cap, e.g. 24 h idle and 30 days absolute; (C) short fixed lifetime, e.g. 8 h; (D) very short idle timeout with a short cap, e.g. 30 min and 12 h.
- **Trade-offs:** A is simple but ignores inactivity. B is convenient and bounds exposure but needs "last used" tracking. C and D are safer but frustrating for a personal dashboard.
- **Recommendation:** B. A dashboard checked daily benefits from sliding expiry, and an absolute cap bounds the risk.
- **Blocks:** FR-SESS-006, ER-SESS-003, SR-SESS-002 (cookie expiry). Scenarios tagged `@blocked-by-OQ-001`: "A request has an expired session", "Missing, expired and revoked sessions are rejected", "Cookie security in production".

## OQ-002 Concurrent sessions per user
- **Status:** **DECIDED by owner, 2026-11-24.**
- **Decision:** Concurrent sessions are allowed. Logout ends only the current session.
- **Why it matters:** affects security posture and the meaning of logout.
- **Options considered:** (A) many concurrent sessions, one per browser; (B) one session, a new sign-in revokes the old; (C) many sessions with a cap and a user-visible list.
- **Trade-offs (record):** A is simplest and matches multi-device use. B limits exposure but surprises users. C adds UI beyond Phase 2.
- **Earlier recommendation:** A (matches the decision).
- **Applied in:** FR-SESS-008, FR-SESS-004; scenarios "A user can be signed in on two browsers at once", "Logout ends only the current session"; assumption A-014.

## OQ-003 SameSite policy and cookie name
- **Status:** OPEN (design stage). **Must assume the frontend and backend are served from the same site (OQ-022).**
- **Why it matters:** the browser returns from GitHub to DevPulse by cross-site navigation. A strict policy may withhold the cookie on that first request, which could break installation callbacks that need the signed-in user. Same-site deployment simplifies ordinary requests but does not remove the cross-site return from GitHub.
- **Options:** (A) Lax; (B) Strict; (C) None with Secure (cross-site cookies); name with or without a host-locking prefix.
- **Trade-offs:** Lax sends the cookie on top-level navigation from GitHub and still blocks most cross-site subrequests. Strict is stronger but risks breaking callbacks. None widens exposure and needs CSRF protection everywhere.
- **Recommendation:** Lax, with a host-locking cookie name in production, verified against the callback flow.
- **Blocks:** SR-SESS-002; scenarios tagged `@blocked-by-OQ-003`: "Cookie security in production", "The user is still signed in when GitHub returns them after installation".

## OQ-004 Session cleanup strategy
- **Status:** OPEN (design stage).
- **Why it matters:** stale session records accumulate. Celery and a scheduler are not allowed before their phase.
- **Options:** (A) delete expired sessions opportunistically during sign-in or lookup; (B) a scheduled job (not available until Phase 9); (C) a database-side scheduled task; (D) keep everything and clean manually.
- **Trade-offs:** A needs no new infrastructure but cleanup is uneven. B is clean but violates phase boundaries now. C adds database operations burden. D accumulates data.
- **Recommendation:** A for Phase 2, revisit in Phase 9.
- **Blocks:** FR-SESS-007; scenario "Expired and revoked sessions are cleaned up".

## OQ-005 One GitHub App or a separate OAuth App plus GitHub App
- **Status:** OPEN (design stage). Preferred direction: one GitHub App, to be confirmed.
- **Why it matters:** decides how many registrations, secrets and consent screens exist, and how identity and installation callbacks work. It may change how many GitHub screens a new user sees between signing in and installing.
- **Options:** (A) one GitHub App for user authorization and installation (preferred direction); (B) an OAuth App for sign-in plus a GitHub App for installation; (C) a GitHub App for installation and a different identity provider (ruled out by the handoff).
- **Trade-offs:** A has one set of credentials and one place for permissions. B separates concerns but doubles secrets and consent. Behavioural differences on GitHub are unverified.
- **Recommendation:** A, confirmed against GitHub documentation in design.
- **Blocks:** the design of every authentication and installation flow; scenarios tagged `@blocked-by-OQ-005`: "The user starts installation", "A successful installation callback is verified and recorded", "A new user signs in and installs the GitHub App".

## OQ-006 Persisting GitHub user access and refresh tokens
- **Status:** **DECIDED by owner, 2026-11-24.**
- **Decision:** GitHub user access and refresh tokens are **not persisted**. Tokens obtained during GitHub user authorization may be used only for the authorization or profile retrieval in progress. Persisting them in a later phase requires a new explicit approval.
- **Why it matters:** persisted tokens are a high-value target but could enable profile refresh without re-authentication.
- **Options considered:** (A) do not persist any user token; (B) persist only the access token, encrypted; (C) persist access and refresh tokens, encrypted, with rotation.
- **Trade-offs (record):** A is safest and simplest but profile refresh must re-authenticate. B and C add encryption, key management, rotation and revocation, and a larger breach impact.
- **Earlier recommendation:** A (matches the decision).
- **Applied in:** SR-CRED-004 (rewritten); scenario "User tokens, if stored, are encrypted" retired; scenario "User tokens are not stored when not needed" kept and reworded.

## OQ-007 Organisation installations in Phase 2
- **Status:** **DECIDED by owner, 2026-11-24.**
- **Decision:** Phase 2 supports **personal GitHub accounts only**. Data requirements must still allow an account-type value other than "User" to be stored.
- **Why it matters:** organisation installs involve owner approval and a different account type. Figma shows an organisation ("acme-engineering"), while the product context says "personal".
- **Options considered:** (A) personal accounts only; (B) personal and organisation accounts.
- **Trade-offs (record):** A is smaller and matches "personal dashboard". B matches the Figma samples but adds approval flows and states.
- **Earlier recommendation:** A (matches the decision).
- **Applied in:** FR-INST-004 retired, "organisation installations" added to non-goals, Organisation owner actor removed, DR-CONN-006 added. What DevPulse does if a callback nevertheless reports an organisation is the new question OQ-023.

## OQ-008 Reconnect after external deletion or suspension
- **Status:** **DECIDED by owner, 2026-11-24.**
- **Decision:** Reconnecting starts a new installation and the old record is kept as history. Suspended installations are not reconnected from DevPulse: the user is offered Manage installation on GitHub.
- **Why it matters:** defines the exits from Installation deleted, Suspended and Disconnected.
- **Options considered:** (A) reconnecting starts a new installation and keeps the old record as history; (B) reconnecting reuses the old record and updates its installation ID; (C) for Suspended there is no reconnect, only "Manage installation" on GitHub.
- **Trade-offs (record):** A keeps history and respects the unique installation ID rule. B loses history. C is accurate because a suspended installation is not reconnected from DevPulse.
- **Earlier recommendation:** A for deleted and disconnected, C for suspended (matches the decision).
- **Applied in:** FR-DISC-005, FR-DISC-006, DR-CONN-005, section 13. The case where a reconnect returns an installation ID that already has a record is the new question OQ-021.

## OQ-009 Failure to remove the installation during disconnection
- **Status:** **DECIDED by owner, 2026-11-24.**
- **Decision:** If GitHub fails to remove the installation, the connection stays Disconnected, is marked "removal pending", and the user is shown safe instructions to remove the App on GitHub.
- **Why it matters:** the user asked to disconnect, but GitHub might refuse or be unreachable.
- **Options considered:** (A) disconnect locally and mark GitHub removal as pending; (B) fail the disconnection, stay Connected and ask to retry; (C) disconnect locally and show instructions to remove the App on GitHub.
- **Trade-offs (record):** A and C honour the user's intent and stop DevPulse reading data, but access remains granted on GitHub. B is strict but traps the user.
- **Earlier recommendation:** C with A's pending marker (matches the decision).
- **Applied in:** ER-DISC-001, DR-CONN-001 (removal-pending marker).

## OQ-010 GitHub App permissions requested
- **Status:** **DECIDED by owner, 2026-11-24.**
- **Decision:** The GitHub App requests only the minimum Phase 2 needs: no repository-content or repository-activity permissions, and no write permissions. Any increase requires explicit owner approval. Because the owner's intent is to show the user's email, read access to the user's email address is part of the Phase 2 minimum; the design stage must verify what GitHub requires for it.
- **Why it matters:** least privilege; any later increase needs explicit approval and may need users to re-consent (unverified on GitHub).
- **Options considered:** (A) only what Phase 2 needs; (B) the full read set planned for the MVP (Figma screen 04); (C) an intermediate set.
- **Trade-offs (record):** A follows least privilege but may require later re-consent when features arrive. B avoids re-consent but over-requests now.
- **Earlier recommendation:** A (matches the decision).
- **Applied in:** SR-PERM-001, FR-STAT-003, FR-STAT-008, scenario "The App requests only the approved minimum permissions".

## OQ-011 Disconnection: uninstall at GitHub or disable locally only
- **Status:** **DECIDED by owner, 2026-11-24.**
- **Decision:** On confirmed disconnection DevPulse first disables repository access locally and sets Disconnected, then asks GitHub to remove the installation.
- **Why it matters:** decides whether disconnecting actually revokes access at GitHub.
- **Options considered:** (A) disable locally only and offer a link to remove the App on GitHub; (B) also remove the installation at GitHub; (C) ask the user which.
- **Trade-offs (record):** A is simple but leaves access granted on GitHub. B truly revokes but needs an authenticated call to GitHub and failure handling (OQ-009). C adds choice and UI.
- **Earlier recommendation:** B with local disabling first (matches the decision).
- **Applied in:** FR-DISC-003, ER-DISC-001, ER-DISC-002.

## OQ-012 Authorization state lifetime and storage
- **Status:** OPEN (design stage). `[REV2]` Decision R2-1 removed the installation-attempt lifetime from this question: Installation required has no expiry. OQ-012 now covers only the authorization (sign-in and profile refresh) state lifetime and storage. How the installation callback's correlation value interacts with Installation required is OQ-024.
- **Why it matters:** governs replay resistance and what a slow user experiences when signing in or refreshing the profile.
- **Options:** (A) server-stored single-use value, bound to the starting browser, with a short lifetime such as 10 minutes; (B) signed self-contained value with expiry; (C) value in a short-lived cookie only.
- **Trade-offs:** A is the strongest against replay and supports single use. B is stateless but harder to make single-use. C is weak without server checking.
- **Recommendation:** A.
- **Blocks:** SR-STATE-001, DR-STATE-001, ER-AUTH-006; scenarios tagged `@blocked-by-OQ-012`: "The callback has an expired state value", "Each authentication failure is explained safely", "A refresh callback with an invalid state value is rejected".

## OQ-013 CSRF protection approach
- **Status:** OPEN (design stage). **Must assume the frontend and backend are served from the same site (OQ-022).**
- **Why it matters:** logout, disconnect, start-installation, start-profile-refresh and re-verification change state using the session cookie. (This is an addition by the document author, not an earlier decision.)
- **Options:** (A) rely on SameSite only; (B) a per-session anti-forgery token; (C) require a custom request header plus an origin check; (D) combine C with SameSite.
- **Trade-offs:** A is fragile (depends on browser behaviour and OQ-003). B is robust but adds token handling in the frontend. C is simple for an API consumed by a single frontend.
- **Recommendation:** D, as defence in depth.
- **Blocks:** SR-CSRF-001; scenarios tagged `@blocked-by-OQ-013`: the forged cross-site logout, disconnection, start-installation, profile-refresh and re-verification scenarios.

## OQ-014 Detecting GitHub-side changes before webhooks exist
- **Status:** **DECIDED by owner, 2026-11-24.**
- **Decision:** DevPulse verifies the connection with GitHub when the user opens Tool Configuration, and the user can request re-verification. Permission attention required, Suspended and Installation deleted are therefore entered only "when DevPulse verifies the connection and GitHub reports ...", never on notification from GitHub (webhooks are a non-goal).
- **Why it matters:** these states can only be shown if DevPulse learns about them. Webhooks arrive in Phase 9.
- **Options considered:** (A) verify when the user opens Tool Configuration; (B) verify at sign-in; (C) a user-triggered "Re-verify" action; (D) only on user action until Phase 9.
- **Trade-offs (record):** A and B keep status current at the cost of GitHub calls and rate use. C gives control but status can be stale. D is simplest and least current.
- **Earlier recommendation:** A plus C (matches the decision).
- **Applied in:** FR-CONF-005 (now Must), FR-CONF-006, FR-STAT-008 to FR-STAT-011, ER-CONF-001.

## OQ-015 Definitions of the early states
- **Status:** **DECIDED by owner, 2026-11-24.**
- **Decision:** "Not configured" is merged into "Authentication completed". There are **eight** connection states. A signed-out visitor has no connection state.
- **Why it matters:** the three early states overlapped.
- **Options considered:** (A) keep three states; (B) merge Authentication completed and Installation required; (C) rename or redefine.
- **Earlier recommendation:** A (the owner chose a different merge).
- **Applied in:** FR-STAT-001, FR-STAT-004 retired, FR-STAT-005, section 13, BR-002, status scenarios, assumptions A-006 and A-007.

## OQ-016 Multiple installations per user (PRD open decision 3)
- **Status:** **DECIDED by owner, 2026-11-24.**
- **Decision:** A user has at most one current connection; earlier disconnected or deleted connections remain on record as history.
- **Options considered:** (A) one active connection per user in Phase 2; (B) several, for example personal plus organisations.
- **Earlier recommendation:** A (matches the decision).
- **Applied in:** DR-CONN-005, FR-STAT-001, assumption A-008.

## OQ-017 Correlating the installation callback to the user who started it
- **Status:** OPEN (design stage).
- **Why it matters:** SR-STATE-002 and ER-INST-003 require it, but how GitHub carries correlation through installation has not been verified.
- **Options:** (A) a single-use value passed through the installation flow and checked on return; (B) rely on the signed-in session plus verifying the installation against the user's GitHub identity; (C) both.
- **Trade-offs:** A is explicit but depends on GitHub carrying the value. B depends on what the user's authorization lets DevPulse check. C is strongest and most work.
- **Recommendation:** C, subject to GitHub documentation.
- **Blocks:** FR-INST-006, SR-STATE-002, ER-INST-003; scenarios tagged `@blocked-by-OQ-017`: "A successful installation callback is verified and recorded", "An installation callback cannot be correlated to the user's request".

## OQ-018 Authorization used for profile refresh
- **Status:** **DECIDED by owner, 2026-11-24.**
- **Decision:** A profile refresh sends the user through GitHub authorization again. Observable behaviour: the user chooses Refresh, is taken to GitHub, returns, and sees updated data and a new refresh time. If the user cancels or GitHub denies, the stored profile is unchanged and a safe message is shown.
- **Options considered:** (A) reuse a stored user token; (B) send the user back through GitHub authorization; (C) refresh only at sign-in.
- **Earlier recommendation:** B if OQ-006 is A (matches the decision).
- **Applied in:** FR-PROF-004, FR-PROF-005, ER-PROF-001, ER-PROF-002, profile scenarios. The inferred consequence ER-PROF-003 (a refresh authorized by a different GitHub account is rejected) is recorded as assumption A-022.

## OQ-019 Which email DevPulse accepts
- **Status:** **DECIDED by owner, 2026-11-24.**
- **Decision:** DevPulse stores the account's primary verified email when GitHub makes it available under the granted authorization; otherwise the public email if available; otherwise none (the existing missing-email behaviour applies).
- **Options considered:** (A) only the primary verified email; (B) only a public email; (C) any authorized email; (D) request no email at all.
- **Earlier recommendation:** A if the permission set allows it, otherwise B (broadly matches).
- **Applied in:** FR-PROF-007, FR-PROF-003, FR-AUTH-004, scenario "The stored email follows the approved source order".

## OQ-020 Account-type values
- **Status:** OPEN (design stage).
- **Why it matters:** the Profile and installation details show an account type. Decision A5 requires that an account-type value other than "User" can be stored (DR-CONN-006).
- **Options:** (A) store whatever GitHub reports; (B) restrict to User and Organization; (C) restrict to User in Phase 2.
- **Trade-offs:** A tolerates new values. B and C give predictable UI.
- **Recommendation:** A, displayed neutrally.
- **Blocks:** DR-USER-002, DR-CONN-006; scenario tagged `@blocked-by-OQ-020`: "A recorded account type other than "User" is shown as recorded".

## OQ-021 `[REV1]` Installation ID that matches a disconnected record
- **Status:** **DECIDED by owner, 2026-11-24** (revision 2), for both parts. The marker sub-question moved to OQ-027.
- **Decision, first part (the user's own disconnected installation ID):** the existing record is **reactivated** as the user's current connection after verification, and updated. Exactly one record exists for that installation ID and the user has at most one current connection. The earlier period is not kept as a separate record in this case. (Decision R2-10; FR-INST-010.)
- **Decision, second part (another user's disconnected record):** the callback is **rejected**, that record is left untouched, the installation is not reassigned, and the signed-in user sees a safe message (consistent with BR-005 and ER-INST-004). (Decision R2-11.)
- **Not decided here:** how a removal-pending marker is cleared. This is OQ-027.
- **Original question:** What happens when a reconnect returns an installation ID that matches the same user's own disconnected record (for example when removal at GitHub was pending), and what happens when a callback reports an installation ID that belongs to another user's disconnected record?
- **Why it matters:** the installation ID must stay unique (DR-CONN-002) and must never be silently reassigned (BR-005), yet the owner wants old connections kept as history (DR-CONN-005).
- **Options for the user's own disconnected record (record):** (A) reactivate the existing record as the current connection and update it; (B) create a new current record and mark the old one superseded; (C) reject the callback and ask the user to remove the App on GitHub first, then try again.
- **Options for another user's disconnected record (record):** (A) reject and leave the record untouched; (B) allow transfer only after GitHub confirms the signed-in user controls the installation account; (C) reject and show support guidance.
- **Trade-offs (record):** reactivating (A) keeps one record per ID and is simple, but history of the earlier period is merged. A superseding record (B) preserves history but complicates uniqueness. Rejecting (C) is safe but may trap users. For other users' records, strict rejection is safest.
- **Earlier recommendation:** A and A (matches the decision).
- **Applied in:** FR-INST-010 (new), ER-INST-004, DR-CONN-005, FR-DISC-005; scenarios "A reconnect returns the user's own disconnected installation ID" and "A callback reports an installation ID that belongs to another user's disconnected record".

## OQ-022 `[REV1]` Deployment topology of frontend and backend
- **Status:** **DECIDED by owner, 2026-11-24.**
- **Decision:** The frontend and the backend are served from the same site. OQ-003 (cookie policy) and OQ-013 (CSRF approach) remain design-stage questions but must assume this.
- **Why it matters:** cookie policy, CSRF protection and cross-origin settings depend on whether browser requests to the backend are same-site or cross-site.
- **Options considered:** (A) same site; (B) different sites (cross-site requests).
- **Trade-offs (record):** A allows stricter cookie handling and simpler forgery protection. B needs cross-site cookies and stronger protection.
- **Applied in:** spec section 0 (P-2), SR-CSRF-001, OQ-003 and OQ-013 notes. Whether local development uses different ports, and how same-site relates to same-origin, are design-stage matters.

## OQ-023 `[REV1]` Behaviour when an installation callback reports an organisation account
- **Status:** **DECIDED by owner, 2026-11-24** (revision 2, decision R2-12).
- **Decision:** the callback is **rejected** with a safe message that only personal GitHub accounts are supported in Phase 2, and **no connection is created** (ER-INST-008). Because no connection is created and the installation is not completed, the state remains as it was before the callback, which is Installation required. That consequence is `[INFERRED]` (assumption A-023) for the owner to confirm.
- **Why it matters:** Phase 2 supports personal accounts only (decision A5), but GitHub's installation page lets the user pick an account, so a callback could report an organisation.
- **Options considered:** (A) reject the callback with a safe message that only personal accounts are supported in Phase 2, and create no connection; (B) record the installation but treat it as unsupported and show a clear state; (C) accept it as a normal connection (conflicts with decision A5).
- **Trade-offs (record):** A keeps scope clean and avoids partial organisation behaviour. B retains data but adds a state outside the eight. C contradicts the decision.
- **Earlier recommendation:** A (matches the decision).
- **Applied in:** ER-INST-008 (new), scenario "An installation callback reports an organisation account". The `@blocked-by-OQ-023` tag is removed from the account-type scenario, which keeps `@blocked-by-OQ-020`.

## OQ-024 `[REV2]` Installation correlation value expired while Installation required
- **Status:** OPEN (design stage). Not decided.
- **Question:** What happens when the user returns to GitHub's installation flow after the correlation value has expired, while the state is still Installation required?
- **Why it matters:** decision R2-1 says Installation required never expires, but the correlation value the installation callback needs (DR-STATE-001, SR-STATE-002) does have an expiry. A user can start installation, leave, and return much later.
- **Options:** (A) reject the callback safely, keep Installation required, and tell the user to start installation again, which issues a new correlation value; (B) accept the callback if the signed-in user and the installation account reported by GitHub can be matched without the expired value (depends on OQ-017); (C) keep the correlation value valid for as long as Installation required lasts, so it never expires (conflicts with the short-lived, single-use rule in SR-STATE-002 and DR-STATE-001).
- **Trade-offs:** A keeps correlation short-lived and single-use and is simple, at the cost of one extra step for a slow user. B is friendlier but relies on a GitHub behaviour that is unverified (A-011) and weakens the correlation guarantee. C removes the problem by weakening replay protection.
- **Recommendation:** A. It keeps the short-lived correlation intact and keeps the state at Installation required, so the user can simply restart installation.
- **Blocks:** scenario tagged `@blocked-by-OQ-024`: "The user returns to GitHub's installation flow after the correlation value has expired". Also related: SR-STATE-002, DR-STATE-001, FR-STAT-006.

## OQ-025 `[REV2]` Repository access in Permission attention required
- **Status:** OPEN (design stage, **to be answered in Phase 3**, when something reads repositories). **Nothing in Phase 2 depends on it.** No scenario is tagged as blocked by it.
- **Question:** In the Permission attention required state, is repository access available?
- **Options:** (A) unavailable; (B) available, but limited to what the granted permissions allow.
- **Trade-offs:** A is simple and safe but stops reading everything while permissions differ. B keeps partial data flowing but needs per-permission handling and a clear freshness message.
- **Recommendation:** none in Phase 2; decided in Phase 3.
- **Applied in:** BR-002 and section 13 state that availability in this state is "not specified in Phase 2 (OQ-025)". FR-STAT-008 and the status scenarios assert nothing about repository access in this state.

## OQ-026 `[REV2]` Time-display details not settled by the example
- **Status:** OPEN (design stage, UI). Decision R2-7: times are displayed exactly in the form of the example "16 Nov 2026, 09:26 UTC" (UI-TIME-001). The scenarios keep the example value. The example does not settle the following; none is decided here.
- **Detail 1: a day with one digit.** Options: (A) no leading zero, "5 Nov 2026"; (B) leading zero, "05 Nov 2026".
- **Detail 2: month name language.** Options: (A) always English abbreviations, "Nov"; (B) follow the browser's language.
- **Detail 3: 12-hour or 24-hour clock.** The example "09:26" reads the same on both. Options: (A) 24-hour clock, for example "14:05"; (B) 12-hour clock with an AM or PM marker.
- **Detail 4: relative times.** The Figma designs show phrases such as "2 minutes ago". The example is an absolute time. Options: (A) show only the absolute form everywhere; (B) allow relative phrases alongside it.
- **Trade-offs:** fixed English and 24-hour forms are predictable and match the example. Following the browser's language or a 12-hour clock suits more users but varies between users.
- **Recommendation:** none; the owner decides.
- **Blocks:** UI-TIME-001 final wording; no scenario is tagged as blocked.

## OQ-027 `[REV2]` How the removal-pending marker is cleared
- **Status:** OPEN (design stage). Not decided. Split out of OQ-021.
- **Question:** After disconnection leaves a connection marked removal pending (ER-DISC-001), how and when is the marker cleared?
- **Why it matters:** when the user reconnects and the existing record is reactivated (FR-INST-010), the marker's value must make sense.
- **Options:** (A) cleared when the existing record is reactivated by a reconnect; (B) cleared when a later check shows GitHub no longer has the installation; (C) cleared by the user acknowledging that they removed the App; (D) never cleared automatically and kept only as history.
- **Trade-offs:** A is simple but says nothing about whether the App was ever removed. B needs a GitHub check for a Disconnected record, which the owner has not asked for. C needs an extra user action. D leaves a permanently stale flag.
- **Recommendation:** A, because a successful verified reconnect shows the App is present and in use again.
- **Blocks:** scenario tagged `@blocked-by-OQ-027`: "The removal-pending marker after a reconnect reactivates the user's own record".

## OQ-028 `[REV2]` Text of the GitHub installation indicator per state
- **Status:** OPEN (design stage, UI). Not decided; **no recommendation given**.
- **Question:** What exact text does the "GitHub installation" indicator (FR-STAT-002) show for each of the eight connection states? The spec does not define it.
- **Why it matters:** the scenario "Authentication and installation are separate indicators" currently covers only five values and is tagged `@blocked-by-OQ-028` until the owner decides.
- **Options (wording per state):**

| State | Wording option 1 | Wording option 2 | Wording option 3 |
|---|---|---|---|
| Authentication completed | Not installed | No installation yet | Not installed yet |
| Installation required | Installation not completed | Waiting for installation | Installation pending |
| Connected | Installed | Active | Installed and verified |
| Permission attention required | Permissions need attention | Installed, permissions need attention | Installed with changed permissions |
| Suspended | Suspended | Suspended on GitHub | Installation suspended |
| Installation deleted | Removed | Removed from GitHub | Not found on GitHub |
| Verification failed | Not verified | Could not be verified | Verification failed |
| Disconnected | Disconnected | Not connected | Disconnected, removal pending (shown only when the marker is set) |

- **Blocks:** scenario tagged `@blocked-by-OQ-028`: "Authentication and installation are separate indicators"; UI-CONF-002 wording for every state.

---

## Revision 2 decisions log (DECIDED by owner, 2026-11-24)

| Decision | Summary | Applied in |
|---|---|---|
| R2-1 | Installation required does not expire; cancelling at GitHub does not change the state; FR-STAT-013 retired | FR-STAT-005, FR-STAT-006, FR-STAT-013 (retired), ER-INST-006, section 13, A-016, A-017, OQ-012, OQ-024 |
| R2-2 | Section 13 matrix stands; Verification failed also offers Manage installation; Installation deleted only Reconnect; owner guidance: standard, reliable, not over-engineered | FR-INST-008, FR-CONF-005, FR-DISC-001, section 13, Design guidance (spec section 0), A-019 |
| R2-3 | Repository access in Permission attention required is not specified in Phase 2 | BR-002, FR-STAT-007, FR-STAT-008, section 13, A-020, OQ-025 |
| R2-4 | A profile refresh authorized by a different GitHub account is rejected | ER-PROF-003, A-022 |
| R2-5 | Verification on opening Tool Configuration happens every time, with no minimum interval | FR-CONF-006 (unchanged), A-018 |
| R2-6 | Temporary GitHub failure during verification: last known state, last verification time, retry option and a visible notice | ER-CONF-001, scenario "GitHub is temporarily unavailable while verifying" |
| R2-7 | Times use exactly the form "16 Nov 2026, 09:26 UTC" | UI-TIME-001, OQ-026 |
| R2-8 | The PRD's Not connected corresponds to Authentication completed | A-021, alias index in `requirements-bdd-coverage.md` |
| R2-9 | FR-CONF-005, FR-INST-008 and FR-DISC-005 are Must | those three requirements |
| R2-10 | A reconnect that returns the user's own disconnected installation ID reactivates the existing record | FR-INST-010, DR-CONN-005, FR-DISC-005, OQ-021 |
| R2-11 | A callback for another user's disconnected installation ID is rejected | ER-INST-004, OQ-021 |
| R2-12 | A callback that reports an organisation account is rejected; no connection is created | ER-INST-008, OQ-023, A-023 |
