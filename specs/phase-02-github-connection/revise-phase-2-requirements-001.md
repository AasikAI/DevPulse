REVISE_PHASE_2_REQUIREMENTS

This is revision 1 of the Phase 2 requirements package. Apply every change below to the files under `specs/phase-02-github-connection/`.

## Ground rules for this revision

- Documentation only. Do not create or modify code, migrations, Compose files, dependencies, tests, design documents, or any file outside the Phase 2 requirements package. Do not delete the `keycloak/` folders in this run.
- Keep requirement IDs stable. Do not renumber. A requirement that no longer applies is kept in place and marked `RETIRED (reason, revision 1)`; new requirements get new IDs appended in their category.
- Mark any requirement or scenario you add or change with `[REV1]` in the Source column or as a tag `@REV1`, so the owner can find every change.
- Anything in this message that you cannot apply without guessing: do not guess. Record it as an open question and say so in your final message.
- When finished, stop at `STATE: AWAITING_REQUIREMENTS_APPROVAL` and end with a change summary table (item, files touched, requirement IDs added, changed, retired).

## A. Owner decisions (record them; they are now decided)

Record each in `open-questions.md` as `DECIDED by owner, 2026-11-24` with the decision text, keep the earlier options and rationale for the record, and update every requirement, scenario, assumption and coverage row that depended on it. Remove `@blocked-by-OQ-...` tags that no longer apply.

1. **Phase 1 gaps (assumption A-001).** The repository lacks several Phase 1 foundations (React Router, Tailwind, ECharts, Vitest, React Testing Library, Playwright, pytest, `backend/tests/`, CI workflow). Decision: these are closed in a separate "Phase 1 completion" step, with its own approval, **before** Phase 2 implementation starts. Add a "Preconditions" section to `spec.md` stating this. Do not specify the Phase 1 completion work in this package.
2. **User tokens (OQ-006, OQ-018).** GitHub user access and refresh tokens are **not persisted**. Rewrite SR-CRED-004 as: tokens obtained during GitHub user authorization may be used only for the authorization or profile retrieval in progress and must not be persisted; persisting them in a later phase requires a new explicit approval. Retire the scenario "User tokens, if stored, are encrypted" (note the reason in the coverage file) and keep "User tokens are not stored when not needed". A profile refresh now sends the user through GitHub authorization again; rewrite FR-PROF-004, FR-PROF-005, ER-PROF-001 and the profile scenarios so the observable behavior is: the user chooses Refresh, is taken to GitHub, returns, and sees updated data and a new refresh time; if the user cancels or GitHub denies, the stored profile is unchanged and a safe message is shown.
3. **Detecting GitHub-side changes (OQ-014).** DevPulse verifies the connection with GitHub when the user opens Tool Configuration, and the user can request re-verification. FR-CONF-005 becomes **Must**. All requirements and scenarios for Permission attention required, Suspended and Installation deleted must be reworded so the trigger is "when DevPulse verifies the connection and GitHub reports ..." and never "when GitHub reports ..." (webhooks are a non-goal). Add a requirement (mark `[INFERRED]`): if GitHub is temporarily unavailable during verification, DevPulse keeps showing the last known state together with its last verification time and a retry option.
4. **Merge "Not configured" into "Authentication completed" (OQ-015).** There are now **eight** connection states: Authentication completed, Installation required, Connected, Permission attention required, Suspended, Installation deleted, Verification failed, Disconnected. Retire FR-STAT-004 and its scenario. A signed-out visitor has no connection state. Update FR-STAT-001, section 13, BR-002, the status scenarios, A-006 and A-007.
5. **Organisation installs (OQ-007).** Phase 2 supports personal GitHub accounts only. Retire FR-INST-004 and its scenario, add "organisation installations" to the non-goals in `spec.md`, and remove the Organisation owner actor. Data requirements must still allow an account-type value other than "User" to be stored.
6. **One connection per user (OQ-016).** Add a data requirement: a user has at most one current connection; earlier disconnected or deleted connections remain on record as history.
7. **Permissions (OQ-010).** The GitHub App requests only the minimum Phase 2 needs: no repository-content or repository-activity permissions, and no write permissions. Any increase requires explicit owner approval. Because the owner's intent is to show the user's email, read access to the user's email address is part of the Phase 2 minimum; the design stage must verify what GitHub requires for it.
8. **Disconnect and reconnect (OQ-008, OQ-009, OQ-011).** On confirmed disconnection DevPulse first disables repository access locally and sets Disconnected, then asks GitHub to remove the installation. If GitHub fails to remove it, the connection stays Disconnected, is marked "removal pending", and the user is shown safe instructions to remove the App on GitHub. Reconnecting starts a new installation and the old record is kept as history. Suspended installations are not reconnected from DevPulse: the user is offered Manage installation on GitHub. Update FR-DISC-003, FR-DISC-005, ER-DISC-001 and the disconnection scenarios.
9. **Email source (OQ-019).** DevPulse stores the account's primary verified email when GitHub makes it available under the granted authorization; otherwise the public email if available; otherwise none (existing missing-email behavior applies).
10. **Concurrent sessions (OQ-002).** Allowed. Logout ends only the current session.
11. **Missing display name.** When GitHub provides no display name, the Profile shows the text "Name not provided by GitHub". Add a requirement FR-PROF-006 and scenarios. Do not fall back to the username.
12. **Deployment topology.** Add a new open question OQ-022 and record it as DECIDED: the frontend and backend are served from the same site. OQ-003 and OQ-013 remain design-stage questions but must assume this.
13. **Housekeeping.** (a) Assumption A-004: the empty `keycloak/` folders may be deleted; record the decision only, do not delete anything in this run. (b) Keep PRD IDs as aliases: they stay in the Source column, and add an alias index (PRD ID to Phase 2 ID) at the end of `requirements-bdd-coverage.md`. (c) Times are displayed in UTC and labelled as UTC: add requirement UI-TIME-001 and one scenario.

New open question to add (not decided): **OQ-021** What happens when a reconnect returns an installation ID that matches the same user's own disconnected record (for example when removal at GitHub was pending), and what happens when a callback reports an installation ID that belongs to another user's disconnected record? Give options, trade-offs and a recommendation, and tag the affected scenarios `@blocked-by-OQ-021`.

## B. Fixes to `spec.md`

1. **BR-002.** Reword it. The rule is: repository access is available only when the user is authenticated and the connection state is Connected; in every other state repository access is unavailable. Mark this `[INFERRED]` so the owner can confirm. Remove the three-combination wording, which contradicts Suspended, Disconnected, Installation deleted and Verification failed.
2. **Repository access per state.** State explicitly, in FR-STAT-008 and FR-STAT-011 and in section 13, that repository access is unavailable in Permission attention required and Verification failed. Section 13 and the FR-STAT requirements must say the same thing for every state.
3. **Installation attempt lifetime.** Define that Installation required applies while an installation attempt is open, and that when the attempt expires without completion the state returns to Authentication completed. The lifetime value is a design-stage parameter linked to OQ-012. Mark the definition `[INFERRED]`.
4. **Exits for every state.** In section 13, make sure every state has at least one valid action and exit that is a Must requirement. In particular, Verification failed must always offer Retry verification (now guaranteed by decision 3).
5. **DR-CONF-001 versus DR-CONN-001.** State explicitly that Tool Configuration metadata is part of the connection's data and not a separate duplicated set. Remove duplicated attributes. Do not name tables.
6. **SR-CSRF-001.** Extend it to cover at least: logout, disconnection, starting installation, starting profile refresh, and re-verification.
7. **Add a requirement** that two simultaneous first sign-ins for the same GitHub account result in exactly one local user.
8. **Update** section 2 (scope), section 4 (non-goals), section 5 (actors), section 13 (states), section 14, section 15 and section 16 for all decisions above. Add a short "Revision history" table at the top.

## C. Fixes to the feature files

1. **Externally caused states.** Reword every scenario for Permission attention required, Suspended and Installation deleted (including those in `phase-02-acceptance`) to the trigger "when DevPulse verifies the connection and GitHub reports ...".
2. **CSRF.** Add forged cross-site request scenarios for starting installation, starting profile refresh and re-verification, in addition to the existing logout and disconnection ones. Remove the `@SR-CSRF-001` tag from "The user starts installation" unless that scenario truly tests forgery.
3. **Actions and exits per state.** Add a Scenario Outline to `tool-configuration.feature` listing, for each of the eight states, which actions are offered and which are not. Add transition scenarios for: Verification failed then successful retry to Connected; Permission attention required then permissions restored to Connected; Suspended then unsuspended and verified to Connected.
4. **Status feature.** Remove the "Not configured" scenario and update the separate-indicators outline to the new combinations. Add the assertion "repository access is not available" to Permission attention required.
5. **Missing display name.** Add scenarios for sign-in and Profile display when GitHub provides no display name.
6. **First-sign-in concurrency.** Add a scenario for two simultaneous first sign-ins creating one user.
7. **Split compound scenarios.** Convert "The Profile handles loading and failure states" and "Tool Configuration handles loading and failure states" into Scenario Outlines with one row per condition.
8. **Make vague scenarios testable.** (a) "When any response, page or error message is produced" becomes an Outline listing the specific surfaces. (b) "When any authentication failure occurs" becomes an Outline over the specific failure kinds in the spec. (c) "No guessable pattern" is restated as an observable assertion; numeric thresholds move to the later design and test plan, and the scenario is tagged `@blocked-by-design`.
9. **Observable outcomes.** "DevPulse retrieves the latest authorized profile data from GitHub" must end with what the user sees (for example the refresh confirmation and the new last-refresh time).
10. **Authorized repository count.** Add a Tool Configuration scenario asserting it is shown when GitHub provides it (FR-CONF-002).
11. **`@blocked-by` tags.** Every scenario that depends on a still-open question must carry `@blocked-by-OQ-nnn`. The open questions that remain are OQ-001, 003, 004, 005, 012, 013, 017, 020 and 021, plus any you add. Remove tags for decided questions.
12. **Time display.** Add one scenario showing times are displayed in UTC and labelled as UTC.

## D. File format

All ten feature files must use the `.feature.md` extension, as defined in section 9.2 of the Phase 2 prompt: a Markdown file with a one-line `#` heading and one fenced `gherkin` block holding the complete Gherkin. Names: `github-authentication`, `authenticated-session`, `github-profile`, `protected-resources`, `github-app-installation`, `tool-configuration`, `github-connection-status`, `github-disconnection`, `credential-protection` and `phase-02-acceptance`, each with `.feature.md`. Replace any bare `.feature` files; leave no duplicates. Update every reference in `spec.md` and `requirements-bdd-coverage.md` (including the "features/*.feature" mention) to the new names.

## E. Bookkeeping files

- `open-questions.md`: mark decided questions as in section A, add OQ-021 and OQ-022, keep OQ-001, 003, 004, 005, 012, 013, 017 and 020 open with their design-stage note.
- `assumptions.md`: resolve A-001, A-004, A-005, A-006, A-007, A-008, A-012, A-013 and A-014 by pointing to the decision; add assumptions for anything you inferred in this revision.
- `requirements-bdd-coverage.md`: regenerate in full. Recount requirements and scenarios. Retired requirements stay in the table as Retired. Replace the generic "why Partial" sentence with a specific explanation per requirement, naming the unspecified behavior and the open question.

## F. Final self-check (report the result)

1. Only files in the Phase 2 requirements package were changed.
2. No requirement or scenario mentions a table, endpoint, class or component.
3. Every requirement maps to a scenario and every scenario to a requirement, both ways.
4. Every `[REV1]` item is listed in the change summary.
5. No decision from section A was changed, softened or reopened.
6. No webhook, Celery, Redis, sync, organisation or repository-activity behavior was added.

Then stop with `STATE: AWAITING_REQUIREMENTS_APPROVAL`.
