REVISE_PHASE_2_REQUIREMENTS

This is revision 2 of the Phase 2 requirements package. Apply every change below to the files under `specs/phase-02-github-connection/`.

## Ground rules for this revision

- Documentation only. Do not create or modify code, migrations, Compose files, dependencies, tests, design documents, or any file outside the Phase 2 requirements package.
- Keep requirement IDs stable. Do not renumber. A requirement or scenario that no longer applies stays in place and is marked `RETIRED (reason, revision 2)`; new items get new IDs appended in their category.
- Mark every item added or changed in this revision with `[REV2]` (requirements, assumptions, questions) or `@REV2` (scenarios). Keep the existing `[REV1]` markers.
- **Do not decide anything that is not written in this message.** If something cannot be applied without guessing, do not guess: record it as an open question, tag the affected scenarios `@blocked-by-OQ-nnn`, and say so in your final message.
- Add a row for revision 2 (2026-11-24) to the revision history in `spec.md`.
- When finished, stop at `STATE: AWAITING_REQUIREMENTS_APPROVAL` and end with a change summary table (item, files touched, requirement IDs added, changed, retired).

## A. Owner decisions (now decided; record them as `DECIDED by owner, 2026-11-24`)

Record each decision in `open-questions.md` or `assumptions.md` as appropriate, keep the earlier options for the record, and update every requirement, scenario, assumption and coverage row that depended on it.

**R2-1. Installation required does not expire.** After the user starts installation, the state is Installation required and it **stays** until installation completes. Cancelling at GitHub does not change the state. The state has no expiry and never returns to Authentication completed by itself.
- Retire FR-STAT-013 and the scenario "An installation attempt expires without completion".
- Reword FR-STAT-005, FR-STAT-006, ER-INST-006, section 13 (Authentication completed and Installation required rows) and the glossary of states so they no longer mention an expiring attempt.
- Authentication completed then means: signed in, no current connection, and installation never started or reconnection never started.
- Resolve assumptions A-016 and A-017 by pointing to this decision. Remove the installation-attempt lifetime from OQ-012; OQ-012 keeps only the authorization state lifetime and storage.
- Do not decide how this interacts with the correlation value that the installation callback needs (DR-STATE-001, SR-STATE-002), which does have an expiry. Record a new open question **OQ-024**: "What happens when the user returns to GitHub's installation flow after the correlation value has expired, while the state is still Installation required?" Give options, trade-offs and a recommendation, and tag affected scenarios `@blocked-by-OQ-024`.

**R2-2. Actions per state.** The section 13 matrix stands, with one change.
- (2a, yes) Verification failed also offers **Manage installation**. The actions there become: Retry verification, Manage installation, Disconnect. Reword FR-INST-008 so Manage installation is also valid when verification could not confirm the installation. Do not claim in the wording that the installation is known to exist in that state.
- (2b, no) Installation deleted still offers only Reconnect.
- Reword FR-CONF-005 and FR-DISC-001 so each applies only in the states where section 13 offers the action (Re-verify and Disconnect: Connected, Permission attention required, Suspended and, as Retry verification, Verification failed; Disconnect also in Verification failed).
- (2c) **Owner guidance:** actions and flows must be standard and reliable, and must not be over-engineered. Add a short "Design guidance" note to `spec.md` recording this. It is guidance, not a requirement. Do not add any action, state or screen beyond those stated.
- Update the Scenario Outline "Each state offers exactly its own actions" (Verification failed row) and resolve assumption A-019 by pointing to this decision.

**R2-3. Repository access in Permission attention required is not specified in Phase 2.** It is decided in Phase 3, when something reads repositories.
- Record a new open question **OQ-025** (design stage, to be answered in Phase 3): options (A) unavailable, (B) available but limited to what the granted permissions allow. State that nothing in Phase 2 depends on it.
- Reword BR-002: repository access is available in Connected; it is unavailable in Authentication completed, Installation required, Suspended, Installation deleted, Verification failed and Disconnected; and its availability in Permission attention required is not specified in Phase 2.
- Remove "must treat repository access as unavailable" from FR-STAT-008 and the "only in this state" phrase from FR-STAT-007 and section 13. In section 13, show repository access for Permission attention required as "Not specified in Phase 2 (OQ-025)".
- In the feature files, remove any assertion about repository access in Permission attention required, remove that row from the outline "Repository access is available only when Connected" (rename it to match), and tag nothing else as blocked by this. Update assumption A-020.
- Do not remove the repository-access assertions for the other states.

**R2-4. Profile refresh authorized by a different GitHub account is rejected** (ER-PROF-003). The stored profile is unchanged and a safe message is shown. Replace `[INFERRED]` with `Decision R2-4` on ER-PROF-003 and resolve assumption A-022.

**R2-5. Verification on opening Tool Configuration happens every time.** FR-CONF-006 stands as written, with no minimum interval between verifications. Resolve assumption A-018. Whether a throttle is added is not a requirement.

**R2-6. Temporary GitHub failure during verification.** Rewrite ER-CONF-001: DevPulse keeps showing the last known state, its last verification time and a retry option, **and** shows a visible notice that the connection could not be verified now. Replace `[INFERRED]` with `Decision R2-6`. Update the scenario "GitHub is temporarily unavailable while verifying" to assert the notice.

**R2-7. Time display format.** UI-TIME-001: times are displayed exactly in the form of the example "16 Nov 2026, 09:26 UTC". Where the example does not settle a detail (for example, a day with one digit, the month name language, 12-hour versus 24-hour clock), do not choose: list each detail in `open-questions.md` as one design-stage UI question (OQ-026) with options. The scenarios keep the example value.

**R2-8. PRD alias.** The PRD's "Not connected" state (FR-GH-005) corresponds to Authentication completed. Resolve assumption A-021, and include this mapping in the alias index at the end of `requirements-bdd-coverage.md`.

**R2-9. Priorities.** FR-CONF-005, FR-INST-008 and FR-DISC-005 are **Must**. Replace "priority raised" wording with `Decision R2-9`.

**R2-10. A reconnect returns the user's own disconnected installation ID** (OQ-021, first part): the existing record is **reactivated** as the user's current connection after verification, and updated. Exactly one record exists for that installation ID, and the user has at most one current connection. The earlier period is not kept as a separate record in this case. Add a requirement for it and rewrite the scenario "A reconnect reports an installation ID that matches the user's own disconnected record" with explicit outcomes. Do **not** decide how the removal-pending marker is cleared; the scenario must not assert anything about the marker. Record that sub-question as a new open question **OQ-027** and tag only a separate marker scenario, if you add one, `@blocked-by-OQ-027`.

**R2-11. A callback reports an installation ID that belongs to another user's disconnected record** (OQ-021, second part): the callback is **rejected**, that record is left untouched, the installation is not reassigned, and the signed-in user sees a safe message (consistent with BR-005 and ER-INST-004). Rewrite the matching scenario with these outcomes and remove `@blocked-by-OQ-021` tags. Mark OQ-021 as DECIDED for both parts, except the marker question, which moves to OQ-027.

**R2-12. An installation callback that reports an organisation account** (OQ-023): the callback is **rejected** with a safe message that only personal GitHub accounts are supported in Phase 2, and **no connection is created**. Add a requirement (ER-INST-008) and a scenario. Because no connection is created and the installation is not completed, the state remains as it was before the callback (Installation required); mark that consequence `[INFERRED]` so the owner can confirm it. Mark OQ-023 DECIDED. Remove `@blocked-by-OQ-023` from the scenario "A recorded account type other than "User" is shown as recorded" and keep `@blocked-by-OQ-020`.

## B. Mechanical fixes (no decision needed)

1. In the Scenario Outline "A refresh callback with an invalid state value is rejected", add a row for "from a browser that did not start the refresh", and tag the scenario `@ER-AUTH-008` as well. SR-STATE-001 lists a mismatched value.
2. The outline "Authentication and installation are separate indicators" covers only five values of the GitHub installation indicator, and the spec does not define the indicator's text for all eight states. Do **not** invent the values. Propose them as options in a new open question **OQ-028** (one row per state, with a few wording options per row, no recommendation), and tag the outline `@blocked-by-OQ-028` until the owner decides.
3. Update spec sections 2, 6 (journeys), 13, 14, 15 and 16 for everything above, and regenerate the counts.

## C. Bookkeeping files

- `open-questions.md`: mark OQ-021 and OQ-023 DECIDED (with the decision text); keep their options for the record. Add OQ-024 to OQ-028 as OPEN. Keep OQ-001, 003, 004, 005, 012, 013, 017 and 020 open.
- `assumptions.md`: resolve A-016, A-017, A-018, A-019, A-020, A-021 and A-022 by pointing to the decision. Add assumptions only for anything you had to infer, each marked `[REV2]` and `[INFERRED]`.
- `requirements-bdd-coverage.md`: regenerate in full. Recount requirements and scenarios. Retired items stay in the table as Retired. Every Partial row gets a specific explanation naming the unspecified behavior and the open question. Include the alias index (PRD ID to Phase 2 ID), including R2-8.

## D. Final self-check (report the result)

1. Only files in the Phase 2 requirements package were changed.
2. No requirement or scenario mentions a table, endpoint, class or component.
3. Every active requirement maps to a scenario and every scenario to a requirement, both ways.
4. Every `[REV2]` item is listed in the change summary.
5. No decision in section A was changed, softened or reopened, and no decision was added that is not in section A.
6. No webhook, Celery, Redis, sync, organisation or repository-activity behavior was added.

Then stop with `STATE: AWAITING_REQUIREMENTS_APPROVAL`.
