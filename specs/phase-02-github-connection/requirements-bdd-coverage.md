# Phase 2: Requirements to BDD Coverage Matrix (revision 2)

Regenerated in full for revision 2 from the requirement tables in `spec.md` and the tags in `features/*.feature.md`. It covers 132 active requirements, 3 retired requirements, 166 active scenarios and 1 retired scenario kept in place. Every active requirement maps to at least one active scenario, and every scenario carries at least one requirement tag. Retired requirements stay in the table as Retired.

| Requirement ID | Priority | Summary | Feature file | Scenario name(s) | Coverage status |
|---|---|---|---|---|---|
| FR-ACC-001 | Must | Protected backend interfaces must reject unauthenticated requests, independently of any frontend route... | protected-resources.feature.md | A signed-in user reaches a protected interface<br>An unauthenticated request to a protected interface is rejected<br>Missing, expired and revoked sessions are rejected | Covered |
| FR-ACC-002 | Must | Protected frontend routes must send an unauthenticated visitor to sign-in instead of showing protected... | protected-resources.feature.md | A signed-in user opens a protected route<br>A visitor opening a protected route is sent to sign-in | Covered |
| FR-ACC-003 | Should | After sign-in, DevPulse should return the user to the in-application route they originally requested. | protected-resources.feature.md | The user returns to the page they first requested | Covered |
| FR-AUTH-001 | Must | DevPulse must allow a visitor to start GitHub authorization from a "Continue with GitHub" action. | github-authentication.feature.md<br>phase-02-acceptance.feature.md | Visitor starts GitHub authorization<br>A new user signs in and installs the GitHub App | Covered |
| FR-AUTH-002 | Must | After successful GitHub authorization, DevPulse must create a local user, or update the existing local user,... | github-authentication.feature.md<br>phase-02-acceptance.feature.md | A new user authenticates<br>An existing user authenticates again without creating a duplicate<br>A new user signs in and installs the GitHub App<br>A returning user with an installation | Covered |
| FR-AUTH-003 | Must | When the authorized GitHub username, display name, avatar or email differs from the stored values, DevPulse... | github-authentication.feature.md | Changed GitHub profile data updates the existing user | Covered |
| FR-AUTH-004 | Must | DevPulse must complete authentication, user creation and session creation when GitHub provides no email. | github-authentication.feature.md<br>phase-02-acceptance.feature.md | GitHub provides no email<br>A user whose GitHub account provides no email | Covered |
| FR-AUTH-005 | Must | DevPulse must record the time of each successful authentication as the user's last login time. | github-authentication.feature.md | A new user authenticates<br>An existing user authenticates again without creating a duplicate | Covered |
| FR-AUTH-006 | Must | When two first sign-ins for the same GitHub account happen at the same time, DevPulse must end with exactly... | github-authentication.feature.md | Two simultaneous first sign-ins create one user | Covered |
| FR-CONF-001 | Must | DevPulse must provide a Tool Configuration area that presents GitHub as a configurable provider with its... | tool-configuration.feature.md | Before installation<br>After installation | Covered |
| FR-CONF-002 | Must | When a connection exists, Tool Configuration must show: provider name, connected GitHub user, installation... | tool-configuration.feature.md | After installation<br>Provider and account details are shown<br>The repository-authorization mode is shown<br>The authorized repository count follows what GitHub provides | Covered |
| FR-CONF-003 | Must | DevPulse must keep the user's Tool Configuration across logout and login. | phase-02-acceptance.feature.md<br>tool-configuration.feature.md | A returning user with an installation<br>The configuration survives logout and login | Covered |
| FR-CONF-004 | Must | Tool Configuration must offer, for the current connection state, exactly the actions listed for that state in... | tool-configuration.feature.md | Each state offers exactly its own actions | Covered |
| FR-CONF-005 | Must | A signed-in user whose connection is Connected, Permission attention required, Suspended or Verification... | tool-configuration.feature.md | Each state offers exactly its own actions<br>The user requests re-verification<br>A successful retry leaves Verification failed<br>Restored permissions leave Permission attention required<br>An unsuspended installation leaves Suspended | Covered |
| FR-CONF-006 | Must | DevPulse must verify the connection with GitHub when the user opens Tool Configuration. | phase-02-acceptance.feature.md<br>tool-configuration.feature.md | A suspended installation<br>A deleted installation<br>A permission change needs attention<br>Opening Tool Configuration verifies the connection<br>Each opening of Tool Configuration verifies the connection | Covered |
| FR-DISC-001 | Must | A user whose connection is Connected, Permission attention required, Suspended or Verification failed must be... | github-disconnection.feature.md<br>tool-configuration.feature.md | The user requests disconnection<br>Each state offers exactly its own actions | Covered |
| FR-DISC-002 | Must | DevPulse must ask the user to confirm disconnection, and cancelling must leave the connection unchanged. | github-disconnection.feature.md | The user is asked to confirm<br>The user cancels disconnection | Covered |
| FR-DISC-003 | Must | On confirmed disconnection, DevPulse must first disable repository access locally, set the state to... | github-disconnection.feature.md<br>phase-02-acceptance.feature.md | The user confirms disconnection<br>Repository access stops before GitHub confirms removal<br>Future repository access is prevented<br>Disconnection preserves the DevPulse session | Covered |
| FR-DISC-004 | Must | Requesting disconnection of an already disconnected connection must complete safely with no change and no... | github-disconnection.feature.md | Disconnecting twice is safe | Covered |
| FR-DISC-005 | Must | A user whose connection is Disconnected or Installation deleted must be able to reconnect. Reconnecting must... | github-disconnection.feature.md<br>phase-02-acceptance.feature.md<br>tool-configuration.feature.md | The user reconnects after disconnecting<br>The user reconnects after the installation was deleted<br>A deleted installation<br>Each state offers exactly its own actions | Covered |
| FR-DISC-006 | Must | DevPulse must not offer reconnection for a Suspended installation. It must offer Manage installation on... | github-disconnection.feature.md<br>tool-configuration.feature.md | A suspended installation is not reconnected from DevPulse<br>Each state offers exactly its own actions | Covered |
| FR-INST-001 | Must | A signed-in user must be able to start installation of the DevPulse GitHub App. | github-app-installation.feature.md<br>phase-02-acceptance.feature.md<br>tool-configuration.feature.md | The user starts installation<br>A new user signs in and installs the GitHub App<br>Each state offers exactly its own actions | Covered |
| FR-INST-002 | Must | DevPulse must support an installation that grants access to all repositories and an installation that grants... | github-app-installation.feature.md<br>tool-configuration.feature.md | The user grants all repositories<br>The user grants selected repositories<br>The repository-authorization mode is shown | Covered |
| FR-INST-003 | Must | DevPulse must support installation on the user's personal GitHub account. Phase 2 supports personal accounts... | github-app-installation.feature.md | The user installs on their personal account | Covered |
| FR-INST-004 | Retired | RETIRED (organisation installations are a Phase 2 non-goal, revision 1). | n/a | n/a (retired) | Retired |
| FR-INST-005 | Must | DevPulse must verify an installation with GitHub before marking it active. | github-app-installation.feature.md<br>github-disconnection.feature.md<br>phase-02-acceptance.feature.md | A successful installation callback is verified and recorded<br>A user has one current connection after reconnecting<br>A new user signs in and installs the GitHub App | Partial |
| FR-INST-006 | Must | DevPulse must associate a verified installation with the signed-in user who started the installation. | github-app-installation.feature.md<br>phase-02-acceptance.feature.md | A successful installation callback is verified and recorded<br>The user is still signed in when GitHub returns them after installation<br>A new user signs in and installs the GitHub App | Partial |
| FR-INST-007 | Must | Receiving the same installation callback more than once must not create duplicate records and must leave a... | github-app-installation.feature.md | A duplicate installation callback creates no duplicate<br>Two identical callbacks arrive at the same time | Covered |
| FR-INST-008 | Must | A user whose connection is Connected, Permission attention required, Suspended or Verification failed must be... | github-app-installation.feature.md<br>github-disconnection.feature.md<br>tool-configuration.feature.md | The user opens GitHub's page to manage the installation<br>A suspended installation is not reconnected from DevPulse<br>Each state offers exactly its own actions | Covered |
| FR-INST-009 | Must | While the state is Authentication completed or Installation required, DevPulse must let the user start, or... | github-app-installation.feature.md<br>tool-configuration.feature.md | The user restarts installation while it is required<br>Each state offers exactly its own actions | Covered |
| FR-INST-010 | Must | When a reconnect returns the installation ID of the user's own Disconnected connection, DevPulse must, after... | github-app-installation.feature.md | A reconnect returns the user's own disconnected installation ID | Covered |
| FR-PROF-001 | Must | DevPulse must retrieve and store the authorized GitHub profile metadata for the user when they authenticate. | github-profile.feature.md | Profile metadata is stored when the user authenticates | Covered |
| FR-PROF-002 | Must | The Profile section must show the user's name, avatar, username, email when available, GitHub profile link,... | github-profile.feature.md | The Profile shows the user's metadata | Covered |
| FR-PROF-003 | Must | When no email is available from GitHub, the Profile must show the text "Email not available from GitHub" and... | github-profile.feature.md<br>phase-02-acceptance.feature.md | The Profile handles a missing email<br>A user whose GitHub account provides no email | Covered |
| FR-PROF-004 | Must | A signed-in user must be able to request a profile refresh. DevPulse must take the user through GitHub... | github-profile.feature.md | The user chooses to refresh the profile<br>A refresh updates changed metadata | Covered |
| FR-PROF-005 | Must | On a successful refresh, DevPulse must update the changed metadata and the last profile refresh time, must... | github-profile.feature.md | A refresh updates changed metadata<br>The user's identity stays stable when the username changes | Covered |
| FR-PROF-006 | Must | When GitHub provides no display name, the Profile must show the text "Name not provided by GitHub" and must... | github-authentication.feature.md<br>github-profile.feature.md | GitHub provides no display name<br>The Profile handles a missing display name | Covered |
| FR-PROF-007 | Must | DevPulse must store the account's primary verified email when GitHub makes it available under the granted... | github-authentication.feature.md | The stored email follows the approved source order | Covered |
| FR-SESS-001 | Must | After successful authentication, DevPulse must create a server-controlled session and deliver its credential... | authenticated-session.feature.md<br>github-authentication.feature.md | A session is created securely at sign-in<br>A new user authenticates | Covered |
| FR-SESS-002 | Must | DevPulse must recognise a valid session after a browser refresh without asking the user to authenticate again. | authenticated-session.feature.md<br>github-app-installation.feature.md<br>phase-02-acceptance.feature.md | The session is restored after a browser refresh<br>The user is still signed in when GitHub returns them after installation<br>A returning user with an installation | Covered |
| FR-SESS-003 | Must | DevPulse must let the signed-in interface retrieve the current user's identity and profile summary using the... | authenticated-session.feature.md | The interface retrieves the current user | Covered |
| FR-SESS-004 | Must | A signed-in user must be able to log out, and logging out must revoke the current DevPulse session. | authenticated-session.feature.md<br>phase-02-acceptance.feature.md | The user logs out<br>Logout ends only the current session<br>Logout preserves the installation | Covered |
| FR-SESS-005 | Must | Logging out when the session is already revoked, expired or absent must complete without error and leave the... | authenticated-session.feature.md | Logging out is idempotent | Covered |
| FR-SESS-006 | Must | DevPulse must never accept an expired session. The lifetime values are an open decision (OQ-001). | authenticated-session.feature.md | A request has an expired session | Partial |
| FR-SESS-007 | Could | DevPulse should remove or retire expired and revoked sessions over time. The strategy is an open decision... | authenticated-session.feature.md | Expired and revoked sessions are cleaned up | Partial |
| FR-SESS-008 | Must | DevPulse must allow the same user to hold more than one session at the same time, and logging out must end... | authenticated-session.feature.md | A user can be signed in on two browsers at once<br>Logout ends only the current session | Covered |
| FR-STAT-001 | Must | DevPulse must represent exactly one of these eight connection states for a signed-in user at any time:... | github-connection-status.feature.md<br>phase-02-acceptance.feature.md | A visitor who is not signed in has no connection state<br>Authentication completed<br>Installation required<br>Connected<br>Repository access is available when Connected and unavailable in the other specified states<br>A user has exactly one state at a time<br>An authenticated user without an installation | Covered |
| FR-STAT-002 | Must | DevPulse must present DevPulse authentication status and GitHub installation status as separate indicators. | github-connection-status.feature.md | Authentication and installation are separate indicators | Partial |
| FR-STAT-003 | Must | DevPulse must show the permission status of a connection by comparing the permissions granted to the... | github-connection-status.feature.md<br>tool-configuration.feature.md | Permission attention required<br>The permission status is shown | Covered |
| FR-STAT-004 | Retired | RETIRED (the Not configured state was merged into Authentication completed, revision 1). | n/a | n/a (retired) | Retired |
| FR-STAT-005 | Must | DevPulse must show Authentication completed for a signed-in user who has no current connection and has never... | github-connection-status.feature.md<br>phase-02-acceptance.feature.md<br>tool-configuration.feature.md | Authentication completed<br>Installation required does not expire<br>A new user signs in and installs the GitHub App<br>An authenticated user without an installation<br>Before installation | Covered |
| FR-STAT-006 | Must | DevPulse must show Installation required from the moment the user starts installation, or starts... | github-app-installation.feature.md<br>github-connection-status.feature.md | The user cancels installation at GitHub<br>The user restarts installation while it is required<br>An installation callback reports an organisation account<br>The user returns to GitHub's installation flow after the correlation value has expired<br>Installation required<br>Installation required does not expire | Covered |
| FR-STAT-007 | Must | DevPulse must show Connected for a verified installation that is active and has the required permissions.... | github-connection-status.feature.md<br>phase-02-acceptance.feature.md | Connected<br>A new user signs in and installs the GitHub App | Covered |
| FR-STAT-008 | Must | When DevPulse verifies the connection and finds that the granted permissions do not match the required... | github-connection-status.feature.md<br>phase-02-acceptance.feature.md<br>tool-configuration.feature.md | Permission attention required<br>A permission change needs attention<br>Restored permissions leave Permission attention required | Covered |
| FR-STAT-009 | Must | When DevPulse verifies the connection and GitHub reports the installation as suspended, DevPulse must show... | github-connection-status.feature.md<br>github-disconnection.feature.md<br>phase-02-acceptance.feature.md<br>tool-configuration.feature.md | Suspended<br>A suspended installation is not reconnected from DevPulse<br>A suspended installation<br>An unsuspended installation leaves Suspended | Covered |
| FR-STAT-010 | Must | When DevPulse verifies the connection and GitHub reports that the installation no longer exists, DevPulse... | github-connection-status.feature.md<br>phase-02-acceptance.feature.md | Installation deleted<br>A deleted installation | Covered |
| FR-STAT-011 | Must | When DevPulse verifies the connection and cannot confirm the installation for a reason other than a temporary... | github-connection-status.feature.md<br>tool-configuration.feature.md | Verification failed<br>Each state offers exactly its own actions<br>A successful retry leaves Verification failed | Covered |
| FR-STAT-012 | Must | DevPulse must show Disconnected after the user disconnects GitHub, and must treat repository access as... | github-connection-status.feature.md | Disconnected | Covered |
| FR-STAT-013 | Retired | RETIRED (Installation required does not expire, revision 2). | n/a | n/a (retired) | Retired |
| SR-AUTHZ-001 | Must | Every user-scoped read and change (profile, connection, configuration, status, disconnection) must be limited... | github-connection-status.feature.md<br>github-disconnection.feature.md<br>github-profile.feature.md<br>protected-resources.feature.md<br>tool-configuration.feature.md | Connection status is private to its owner<br>A user cannot disconnect another user's connection<br>One user cannot read another user's profile<br>A user cannot access another user's protected data<br>Each user sees only their own configuration | Covered |
| SR-CRED-001 | Must | The DevPulse session credential must be random, high-entropy and opaque, and only a cryptographic hash of it... | credential-protection.feature.md | The raw session credential is never stored<br>Session credentials cannot be predicted | Partial |
| SR-CRED-002 | Must | The GitHub App private key must never be stored in normal PostgreSQL application tables, and must never be... | credential-protection.feature.md | The private key is not in normal database tables<br>The private key is never returned or shown | Covered |
| SR-CRED-003 | Must | GitHub installation access tokens must be short-lived, generated only when an approved GitHub operation needs... | credential-protection.feature.md | Installation access is short-lived | Covered |
| SR-CRED-004 | Must | Tokens obtained during GitHub user authorization may be used only for the authorization or profile retrieval... | credential-protection.feature.md | User tokens are not stored when not needed | Covered |
| SR-CRED-005 | Must | Credentials must not appear in browser local storage, browser session storage, JavaScript-readable cookies,... | credential-protection.feature.md<br>github-profile.feature.md | No token appears in what the browser receives<br>No credential is kept in browser storage<br>The private key is never returned or shown<br>Errors and URLs contain no credential<br>Profile data exposes no credential | Covered |
| SR-CRED-006 | Must | Credentials, authorization headers and cookies must be redacted from logs. When background jobs are... | credential-protection.feature.md | Logs contain no secrets | Covered |
| SR-CSRF-001 | Must | State-changing requests that rely on the session cookie must be protected against cross-site request forgery.... | authenticated-session.feature.md<br>github-app-installation.feature.md<br>github-disconnection.feature.md<br>github-profile.feature.md<br>tool-configuration.feature.md | A forged cross-site logout is rejected<br>A forged cross-site request to start installation is rejected<br>A forged cross-site disconnection is rejected<br>A forged cross-site profile refresh is rejected<br>A forged cross-site re-verification request is rejected | Partial |
| SR-ERR-001 | Must | User-visible errors must be safe and actionable, and must not contain stack traces, raw GitHub error content,... | credential-protection.feature.md<br>github-authentication.feature.md<br>github-disconnection.feature.md | Errors and URLs contain no credential<br>Each authentication failure is explained safely<br>Removing the installation at GitHub fails during disconnection | Covered |
| SR-PERM-001 | Must | The GitHub App must request only the minimum permissions Phase 2 needs. It must request no repository-content... | github-app-installation.feature.md | The App requests only the approved minimum permissions | Covered |
| SR-PRIV-001 | Could | DevPulse should store only the profile attributes listed in DR-USER-002 and must not store GitHub attributes... | github-profile.feature.md | Only the approved profile attributes are stored | Covered |
| SR-REDIR-001 | Must | A post-login destination must be limited to known in-application routes. An arbitrary or external destination... | protected-resources.feature.md | Unsafe post-login destinations are ignored | Covered |
| SR-SESS-001 | Must | DevPulse must issue a new session credential at every successful authentication and must not honour any... | authenticated-session.feature.md | Signing in issues a new session credential | Covered |
| SR-SESS-002 | Must | The session cookie must be HTTP-only; in production it must also be Secure and use an approved SameSite... | authenticated-session.feature.md | A session is created securely at sign-in<br>Cookie security in production | Partial |
| SR-STATE-001 | Must | Every authorization callback, for sign-in and for profile refresh, must be accepted only with a short-lived,... | credential-protection.feature.md<br>github-authentication.feature.md<br>github-profile.feature.md | Replayed callbacks are rejected<br>The callback has no authorization code<br>The callback has no state value<br>The callback has an unknown state value<br>The callback has an expired state value<br>The callback reuses a state value<br>The state value belongs to a different browser<br>A refresh callback with an invalid state value is rejected | Partial |
| SR-STATE-002 | Must | The installation callback must be accepted only when it can be correlated to an installation that the... | credential-protection.feature.md<br>github-app-installation.feature.md | Replayed callbacks are rejected<br>The user returns to GitHub's installation flow after the correlation value has expired<br>A successful installation callback is verified and recorded<br>An installation callback cannot be correlated to the user's request | Partial |
| DR-CONF-001 | Must | Tool Configuration metadata (the provider, the configuration status and the last verification time) is part... | github-app-installation.feature.md<br>tool-configuration.feature.md | A successful installation callback is verified and recorded<br>The configuration survives logout and login | Covered |
| DR-CONN-001 | Must | DevPulse must keep, for each connection: internal connection ID, owning DevPulse user, provider, GitHub... | github-app-installation.feature.md<br>github-disconnection.feature.md | The user installs on their personal account<br>A successful installation callback is verified and recorded<br>The removal-pending marker after a reconnect reactivates the user's own record<br>The user confirms disconnection | Covered |
| DR-CONN-002 | Must | A GitHub installation ID must be unique across all DevPulse users. | github-app-installation.feature.md | A duplicate installation callback creates no duplicate<br>Two identical callbacks arrive at the same time<br>A reconnect returns the user's own disconnected installation ID<br>A callback reports an installation ID that belongs to another user's disconnected record | Covered |
| DR-CONN-003 | Must | Each connection must belong to exactly one DevPulse user. | github-app-installation.feature.md | A successful installation callback is verified and recorded | Partial |
| DR-CONN-004 | Must | A disconnected connection must remain on record with its disconnection time. | github-disconnection.feature.md | The user confirms disconnection | Covered |
| DR-CONN-005 | Must | A user must have at most one current connection. Earlier Disconnected or Installation deleted connections... | github-app-installation.feature.md<br>github-disconnection.feature.md | A reconnect returns the user's own disconnected installation ID<br>The user reconnects after disconnecting<br>The user reconnects after the installation was deleted<br>A user has one current connection after reconnecting | Covered |
| DR-CONN-006 | Must | DevPulse must be able to store an account-type value other than "User" for the user and for the installation... | github-app-installation.feature.md | A recorded account type other than "User" is shown as recorded | Partial |
| DR-SESS-001 | Must | DevPulse must keep, for each session: the owning user, a hash of the credential, creation time, expiry time... | authenticated-session.feature.md<br>credential-protection.feature.md | A session is created securely at sign-in<br>The raw session credential is never stored | Covered |
| DR-STATE-001 | Must | DevPulse must keep authorization and installation correlation values with an expiry and a consumed marker so... | credential-protection.feature.md<br>github-app-installation.feature.md<br>github-authentication.feature.md | Replayed callbacks are rejected<br>The user returns to GitHub's installation flow after the correlation value has expired<br>The callback has an expired state value<br>The callback reuses a state value | Partial |
| DR-USER-001 | Must | DevPulse must keep at most one local user per stable GitHub user ID. | github-authentication.feature.md<br>github-profile.feature.md | A new user authenticates<br>An existing user authenticates again without creating a duplicate<br>Two simultaneous first sign-ins create one user<br>The user's identity stays stable when the username changes | Covered |
| DR-USER-002 | Must | DevPulse must keep, for each user: stable GitHub user ID, username, display name when available, avatar... | github-authentication.feature.md<br>github-profile.feature.md | Changed GitHub profile data updates the existing user<br>The stored email follows the approved source order<br>GitHub provides no display name<br>Profile metadata is stored when the user authenticates | Covered |
| DR-USER-003 | Must | DevPulse must store all times as timezone-aware UTC values. | github-profile.feature.md | Profile metadata is stored when the user authenticates | Covered |
| UI-A11Y-001 | Must | Every control in these pages must be reachable and operable by keyboard, have visible focus and an accessible... | tool-configuration.feature.md | Tool Configuration can be used by keyboard | Covered |
| UI-AUTH-001 | Must | The sign-in page must offer GitHub as the only way to sign in and must not show email or password fields. | github-authentication.feature.md | Visitor starts GitHub authorization<br>Sign-in offers GitHub only | Covered |
| UI-AUTH-002 | Must | When authentication fails, the sign-in page must show a safe message that says what happened and offer a... | github-authentication.feature.md | Each authentication failure is explained safely | Partial |
| UI-CONF-001 | Must | Tool Configuration must show no synchronization controls and no synchronization status. | phase-02-acceptance.feature.md<br>tool-configuration.feature.md | Phase 2 performs no repository-activity synchronization<br>Tool Configuration has no synchronization controls | Covered |
| UI-CONF-002 | Must | Every status must be conveyed with text, not by colour alone. | tool-configuration.feature.md | Status is never conveyed by colour alone | Covered |
| UI-NAV-001 | Should | Authenticated navigation items (Profile, Tool Configuration, logout) must not be offered to a visitor. | protected-resources.feature.md | A visitor is not offered authenticated navigation | Covered |
| UI-PROF-001 | Must | The Profile must be a section of its own, separate from Tool Configuration, and reachable from authenticated... | github-profile.feature.md | The Profile shows the user's metadata | Covered |
| UI-PROF-002 | Could | Where the Profile hints at later phases, it may show only the neutral placeholder "Not yet synchronized". | github-profile.feature.md | A neutral placeholder hints at later phases | Covered |
| UI-STATE-001 | Must | Pages in this phase must provide loading, success, recoverable-error and backend-unavailable states. | github-profile.feature.md<br>protected-resources.feature.md<br>tool-configuration.feature.md | The Profile handles each loading and failure condition<br>The backend is unavailable<br>A page shows a loading state, then its content<br>Tool Configuration handles each loading and failure condition | Covered |
| UI-TIME-001 | Must | Every time shown to the user must be displayed in UTC, labelled as UTC, and in exactly the form of the... | github-profile.feature.md | Times are displayed in UTC and labelled as UTC | Covered |
| BR-001 | Must | The stable GitHub user ID is the only identity key. Username, display name and email must never identify a... | github-authentication.feature.md<br>github-profile.feature.md | A new user authenticates<br>An existing user authenticates again without creating a duplicate<br>Two simultaneous first sign-ins create one user<br>The user's identity stays stable when the username changes<br>A refresh authorized by a different GitHub account is rejected | Covered |
| BR-002 | Must | Repository access is available when the user is authenticated and the connection state is Connected. It is... | github-app-installation.feature.md<br>github-connection-status.feature.md<br>github-disconnection.feature.md<br>phase-02-acceptance.feature.md | A successful installation callback is verified and recorded<br>Connected<br>Suspended<br>Installation deleted<br>Verification failed<br>Disconnected<br>Authentication and installation are separate indicators<br>Repository access is available when Connected and unavailable in the other specified states<br>Repository access stops before GitHub confirms removal<br>A new user signs in and installs the GitHub App | Covered |
| BR-003 | Must | Logging out must not change or remove the GitHub App installation. | authenticated-session.feature.md<br>phase-02-acceptance.feature.md | Logout leaves the GitHub installation in place<br>Logout preserves the installation | Covered |
| BR-004 | Must | Disconnecting GitHub must not end the DevPulse session. | github-disconnection.feature.md<br>phase-02-acceptance.feature.md | The DevPulse session is preserved<br>Disconnection preserves the DevPulse session | Covered |
| BR-005 | Must | A GitHub installation ID belongs to at most one DevPulse user and must never be silently reassigned to... | github-app-installation.feature.md | The installation is already owned by another user<br>A callback reports an installation ID that belongs to another user's disconnected record | Covered |
| BR-006 | Must | Phase 2 must not retrieve or store repository activity of any kind. | phase-02-acceptance.feature.md<br>tool-configuration.feature.md | Phase 2 performs no repository-activity synchronization<br>Tool Configuration has no synchronization controls | Covered |
| BR-007 | Must | DevPulse must use neutral, evidence-based language and must not present profile or connection data as a... | phase-02-acceptance.feature.md | DevPulse uses neutral language | Covered |
| BR-008 | Must | DevPulse must never invent an email for a user. | github-authentication.feature.md<br>github-profile.feature.md<br>phase-02-acceptance.feature.md | GitHub provides no email<br>The stored email follows the approved source order<br>The Profile handles a missing email<br>A user whose GitHub account provides no email | Covered |
| ER-ACC-001 | Must | A protected backend request without a valid session must receive an authentication-required response that... | protected-resources.feature.md | An unauthenticated request to a protected interface is rejected<br>Missing, expired and revoked sessions are rejected | Covered |
| ER-AUTH-001 | Must | When the user cancels at GitHub, DevPulse must create no session, leave the visitor unauthenticated, and... | github-authentication.feature.md | The visitor cancels at GitHub | Covered |
| ER-AUTH-002 | Must | When GitHub denies authorization, DevPulse must create no session and must show a safe explanation. | github-authentication.feature.md | GitHub denies authorization | Covered |
| ER-AUTH-003 | Must | When the authorization callback has no authorization code, DevPulse must reject it and create no session. | github-authentication.feature.md | The callback has no authorization code | Covered |
| ER-AUTH-004 | Must | When the authorization callback has no state value, DevPulse must reject it and create no session. | github-authentication.feature.md<br>github-profile.feature.md | The callback has no state value<br>A refresh callback with an invalid state value is rejected | Covered |
| ER-AUTH-005 | Must | When the state value is unknown to DevPulse, DevPulse must reject the callback and create no session. | github-authentication.feature.md<br>github-profile.feature.md | The callback has an unknown state value<br>A refresh callback with an invalid state value is rejected | Covered |
| ER-AUTH-006 | Must | When the state value has expired, DevPulse must reject the callback and create no session. | github-authentication.feature.md<br>github-profile.feature.md | The callback has an expired state value<br>A refresh callback with an invalid state value is rejected | Partial |
| ER-AUTH-007 | Must | When the state value was already used, DevPulse must reject the callback and create no session. | github-authentication.feature.md<br>github-profile.feature.md | The callback reuses a state value<br>A refresh callback with an invalid state value is rejected | Covered |
| ER-AUTH-008 | Must | When the state value does not belong to the browser that started authorization, DevPulse must reject the... | github-authentication.feature.md<br>github-profile.feature.md | The state value belongs to a different browser<br>A refresh callback with an invalid state value is rejected | Covered |
| ER-AUTH-009 | Must | When GitHub is temporarily unavailable during authentication, DevPulse must create no session, show a... | github-authentication.feature.md | GitHub is temporarily unavailable during authentication | Covered |
| ER-CONF-001 | Must | When GitHub is temporarily unavailable while DevPulse verifies an existing connection, DevPulse must keep... | tool-configuration.feature.md | GitHub is temporarily unavailable while verifying | Covered |
| ER-DISC-001 | Must | When GitHub fails to remove the installation after disconnection, the connection must stay Disconnected and... | github-disconnection.feature.md | Removing the installation at GitHub fails during disconnection | Covered |
| ER-DISC-002 | Must | When the installation is already removed at GitHub, disconnection must still complete and leave the... | github-disconnection.feature.md | The installation is already removed at GitHub | Covered |
| ER-INST-001 | Must | An installation callback with no valid DevPulse session must not be associated with any user. | github-app-installation.feature.md | An installation callback with no session is not associated with anyone | Covered |
| ER-INST-002 | Must | An installation callback with no installation ID must be rejected and must create no installation record. | github-app-installation.feature.md | An installation callback has no installation ID | Covered |
| ER-INST-003 | Must | An installation callback that cannot be correlated to an installation the user started must be rejected and... | github-app-installation.feature.md | An installation callback cannot be correlated to the user's request | Partial |
| ER-INST-004 | Must | An installation callback for an installation ID that belongs to another user, whether that user's record is... | github-app-installation.feature.md | The installation is already owned by another user<br>A callback reports an installation ID that belongs to another user's disconnected record | Covered |
| ER-INST-005 | Must | When verification does not confirm the installation, DevPulse must not mark it active and must show... | github-app-installation.feature.md | Verification does not confirm the installation | Covered |
| ER-INST-006 | Must | When the user cancels installation at GitHub, DevPulse must create no connection, keep the user signed in and... | github-app-installation.feature.md | The user cancels installation at GitHub | Covered |
| ER-INST-007 | Must | When GitHub is temporarily unavailable during verification of an installation callback, DevPulse must not... | github-app-installation.feature.md | GitHub is temporarily unavailable during verification | Covered |
| ER-INST-008 | Must | An installation callback that reports an organisation account must be rejected with a safe message that only... | github-app-installation.feature.md | An installation callback reports an organisation account | Covered |
| ER-PROF-001 | Must | When the user cancels at GitHub, or GitHub denies authorization, during a profile refresh, DevPulse must... | github-profile.feature.md | The user cancels at GitHub during a refresh<br>GitHub denies authorization during a refresh | Covered |
| ER-PROF-002 | Must | When a profile refresh fails temporarily because GitHub is unavailable, DevPulse must keep the stored... | github-profile.feature.md | The refresh fails temporarily | Covered |
| ER-PROF-003 | Must | When the GitHub account that authorizes a profile refresh is not the signed-in user's GitHub account,... | github-profile.feature.md | A refresh authorized by a different GitHub account is rejected | Covered |
| ER-SESS-001 | Must | A request with no session must be treated as unauthenticated. | authenticated-session.feature.md<br>protected-resources.feature.md | A request has no session<br>Missing, expired and revoked sessions are rejected | Covered |
| ER-SESS-002 | Must | A request with an unrecognised or malformed session credential must be treated as unauthenticated. | authenticated-session.feature.md | A request has a malformed or unrecognised session credential | Covered |
| ER-SESS-003 | Must | A request with an expired session must be treated as unauthenticated. | authenticated-session.feature.md<br>protected-resources.feature.md | A request has an expired session<br>Missing, expired and revoked sessions are rejected | Partial |
| ER-SESS-004 | Must | A request with a revoked session must be treated as unauthenticated. | authenticated-session.feature.md<br>protected-resources.feature.md | A request has a revoked session<br>Missing, expired and revoked sessions are rejected | Covered |
| ER-SYS-001 | Must | When the backend is unavailable, the interface must show a safe unavailable state and must not show stale... | github-profile.feature.md<br>protected-resources.feature.md<br>tool-configuration.feature.md | The Profile handles each loading and failure condition<br>The backend is unavailable<br>Tool Configuration handles each loading and failure condition | Covered |
| ER-SYS-002 | Should | When GitHub rate-limits authentication, verification or refresh, DevPulse must show a safe retry-later... | github-app-installation.feature.md<br>github-authentication.feature.md<br>github-profile.feature.md | GitHub rate-limits verification<br>GitHub rate-limits authentication<br>GitHub rate-limits a refresh | Covered |

## Partial coverage: specific reasons

A Partial row has at least one scenario, but part of the behaviour it requires is not yet specified. Each row names that behaviour and the open question that settles it. The matching scenarios carry a `@blocked-by-OQ-nnn` tag (or `@blocked-by-design`).

| Requirement ID | Behaviour not yet specified | Open question(s) |
|---|---|---|
| FR-INST-005 | Verification before activation is specified. How the callback reaches DevPulse and is tied to the user depends on one-versus-two GitHub Apps and on callback correlation. | OQ-005, OQ-017 |
| FR-INST-006 | Association with the signed-in user is specified. It depends on how the user is correlated on return from GitHub, on whether the session cookie is sent on that return, and on one-versus-two GitHub Apps. | OQ-003, OQ-005, OQ-017 |
| FR-SESS-006 | Never accepting an expired session is specified. The lifetime values and expiry model are not specified. | OQ-001 |
| FR-SESS-007 | That cleanup happens is specified. When, how and by what mechanism it runs is not specified, and no scheduler is allowed in Phase 2. | OQ-004 |
| FR-STAT-002 | Separate authentication and installation indicators are specified. The text of the GitHub installation indicator for each of the eight states is not specified; the scenario covers only five values and waits for the owner's wording. | OQ-028 |
| SR-CRED-001 | Hash-only storage is tested. Unpredictability is stated as an observable assertion, but the entropy size and test thresholds are left to the design and test plan. | design stage |
| SR-CSRF-001 | Rejection of forged cross-site requests is specified for logout, disconnection, starting installation, starting a profile refresh and re-verification. The protection approach, and so how a forged request is built in a test, is not specified. | OQ-013 |
| SR-SESS-002 | HTTP-only, Secure and time-limited are specified. The SameSite policy, the cookie name and the lifetime value are not specified. | OQ-001, OQ-003 |
| SR-STATE-001 | Rejection of missing, unknown, reused and mismatched state values is specified. The state lifetime that decides when a value counts as expired is not specified. | OQ-012 |
| SR-STATE-002 | Installation correlation is specified as a rule. The mechanism, how it differs with one-versus-two GitHub Apps, and what happens when the correlation value has expired while Installation required are not specified. | OQ-005, OQ-017, OQ-024 |
| DR-CONN-003 | Ownership of a verified installation is exercised only by the installation-callback scenario, whose journey depends on one-versus-two GitHub Apps and on how the callback is correlated to the user. | OQ-005, OQ-017 |
| DR-CONN-006 | Storing an account type other than User is specified. How such a value is displayed is not specified. | OQ-020 |
| DR-STATE-001 | Single use is specified and tested. The expiry value, where the correlation value is kept, and what happens when the installation correlation value has expired while Installation required are not specified. | OQ-012, OQ-024 |
| UI-AUTH-002 | Safe messages are specified for every failure kind. The expired-state row cannot be finalised until the state lifetime is decided. | OQ-012 |
| ER-AUTH-006 | Rejection of an expired state value is specified. The state lifetime is not specified, so the scenario cannot say how long is too long. | OQ-012 |
| ER-INST-003 | Rejection of an uncorrelated callback is specified. How GitHub carries correlation through installation is unverified, so what counts as correlated is not specified. | OQ-017 |
| ER-SESS-003 | Rejection of an expired session is specified. The session lifetime and whether expiry is fixed or sliding are not specified. | OQ-001 |

Revision 2 note: OQ-025 (repository access in Permission attention required) blocks no requirement and no scenario, because nothing in Phase 2 depends on it. OQ-021 and OQ-023 are decided and no longer block anything.

Requirements that were Partial in revision 1 and are now Covered: BR-005, DR-CONN-002, DR-CONN-005 and ER-INST-004 (OQ-021 decided, R2-10 and R2-11). FR-STAT-013 is retired.

## Retired requirements and scenarios

| Item | Kind | Reason |
|---|---|---|
| FR-STAT-013 | Requirement (revision 2) | Decision R2-1: Installation required does not expire, so there is no expiring attempt. |
| "An installation attempt expires without completion" (github-app-installation) | Scenario (revision 2), kept in place and tagged `@RETIRED` | Follows FR-STAT-013. Not counted as active. |
| FR-STAT-004 | Requirement (revision 1) | Decision A4: Not configured is merged into Authentication completed. |
| FR-INST-004 | Requirement (revision 1) | Decision A5: organisation installations are a Phase 2 non-goal. |
| "Not configured", "The user installs on an organisation account", "User tokens, if stored, are encrypted" | Scenarios removed in revision 1 | Followed FR-STAT-004, FR-INST-004 and decision A2 respectively. |
| "Manage installation is offered for a connected installation", "Reconnection is offered after disconnection", "The user refreshes the profile", "GitHub no longer authorizes the refresh" | Scenarios replaced in revision 1 | Superseded by the all-states action outline and by the redirect-based refresh scenarios. |

## Scenarios per feature file

| Feature file | Active scenarios | Added or changed in revision 1 | Added or changed in revision 2 |
|---|---|---|---|
| authenticated-session.feature.md | 16 | 2 | 0 |
| credential-protection.feature.md | 11 | 3 | 0 |
| github-app-installation.feature.md | 26 | 4 | 8 |
| github-authentication.feature.md | 20 | 4 | 0 |
| github-connection-status.feature.md | 14 | 4 | 6 |
| github-disconnection.feature.md | 16 | 5 | 2 |
| github-profile.feature.md | 20 | 11 | 1 |
| phase-02-acceptance.feature.md | 11 | 4 | 1 |
| protected-resources.feature.md | 11 | 0 | 0 |
| tool-configuration.feature.md | 21 | 8 | 4 |
| **Total** | **166** | **45** | **22** |

## Coverage summary

| Category | Active requirements | Retired |
|---|---|---|
| Functional (FR) | 56 | 3 |
| Security (SR) | 16 | 0 |
| Data (DR) | 12 | 0 |
| Interface (UI) | 10 | 0 |
| Business rule (BR) | 8 | 0 |
| Error condition (ER) | 30 | 0 |
| **Total** | **132** | **3** |

- Covered: 115
- Partial: 17
- Gap: 0
- Retired: 3

### Gaps

None. Every active requirement has at least one active scenario.

### Scenarios with no requirement

None. Every scenario is tagged with at least one requirement ID.

## Change index

### Revision 1 requirements (`[REV1]`)

| Requirement ID | Kind in revision 1 |
|---|---|
| FR-AUTH-006 | Added |
| FR-CONF-004 | Changed |
| FR-CONF-005 | Changed |
| FR-CONF-006 | Added |
| FR-DISC-003 | Changed |
| FR-DISC-005 | Changed |
| FR-DISC-006 | Added |
| FR-INST-003 | Changed |
| FR-INST-004 | Retired |
| FR-INST-008 | Changed |
| FR-INST-009 | Added |
| FR-PROF-004 | Changed |
| FR-PROF-005 | Changed |
| FR-PROF-006 | Added |
| FR-PROF-007 | Added |
| FR-SESS-008 | Added |
| FR-STAT-001 | Changed |
| FR-STAT-003 | Changed |
| FR-STAT-004 | Retired |
| FR-STAT-005 | Changed |
| FR-STAT-006 | Changed |
| FR-STAT-008 | Changed |
| FR-STAT-009 | Changed |
| FR-STAT-010 | Changed |
| FR-STAT-011 | Changed |
| FR-STAT-013 | Added |
| SR-CRED-004 | Changed |
| SR-CSRF-001 | Changed |
| SR-PERM-001 | Changed |
| SR-STATE-001 | Changed |
| DR-CONF-001 | Changed |
| DR-CONN-001 | Changed |
| DR-CONN-005 | Added |
| DR-CONN-006 | Added |
| UI-TIME-001 | Added |
| BR-002 | Changed |
| ER-CONF-001 | Added |
| ER-DISC-001 | Changed |
| ER-INST-006 | Changed |
| ER-PROF-001 | Changed |
| ER-PROF-002 | Changed |
| ER-PROF-003 | Added |

### Revision 2 requirements (`[REV2]`)

| Requirement ID | Kind in revision 2 |
|---|---|
| FR-CONF-005 | Changed |
| FR-DISC-001 | Changed |
| FR-DISC-005 | Changed |
| FR-INST-008 | Changed |
| FR-INST-010 | Added |
| FR-STAT-005 | Changed |
| FR-STAT-006 | Changed |
| FR-STAT-007 | Changed |
| FR-STAT-008 | Changed |
| FR-STAT-013 | Retired |
| DR-CONN-005 | Changed |
| UI-TIME-001 | Changed |
| BR-002 | Changed |
| ER-CONF-001 | Changed |
| ER-INST-004 | Changed |
| ER-INST-006 | Changed |
| ER-INST-008 | Added |
| ER-PROF-003 | Changed |

### Scenarios added or changed in revision 2 (`@REV2`)

| Feature file | Scenario |
|---|---|
| github-app-installation.feature.md | The user cancels installation at GitHub |
| github-app-installation.feature.md | An installation attempt expires without completion (retired) |
| github-app-installation.feature.md | An installation callback reports an organisation account |
| github-app-installation.feature.md | The user returns to GitHub's installation flow after the correlation value has expired |
| github-app-installation.feature.md | A reconnect returns the user's own disconnected installation ID |
| github-app-installation.feature.md | The removal-pending marker after a reconnect reactivates the user's own record |
| github-app-installation.feature.md | A callback reports an installation ID that belongs to another user's disconnected record |
| github-app-installation.feature.md | The user opens GitHub's page to manage the installation |
| github-app-installation.feature.md | A recorded account type other than "User" is shown as recorded |
| github-connection-status.feature.md | Authentication completed |
| github-connection-status.feature.md | Installation required |
| github-connection-status.feature.md | Installation required does not expire |
| github-connection-status.feature.md | Permission attention required |
| github-connection-status.feature.md | Authentication and installation are separate indicators |
| github-connection-status.feature.md | Repository access is available when Connected and unavailable in the other specified states |
| github-disconnection.feature.md | The user reconnects after disconnecting |
| github-disconnection.feature.md | The user reconnects after the installation was deleted |
| github-profile.feature.md | A refresh callback with an invalid state value is rejected |
| phase-02-acceptance.feature.md | A permission change needs attention |
| tool-configuration.feature.md | Before installation |
| tool-configuration.feature.md | Each state offers exactly its own actions |
| tool-configuration.feature.md | Each opening of Tool Configuration verifies the connection |
| tool-configuration.feature.md | GitHub is temporarily unavailable while verifying |

### Scenarios added or changed in revision 1 and not touched again (`@REV1`)

| Feature file | Scenario |
|---|---|
| authenticated-session.feature.md | A user can be signed in on two browsers at once |
| authenticated-session.feature.md | Logout ends only the current session |
| credential-protection.feature.md | Session credentials cannot be predicted |
| credential-protection.feature.md | The private key is never returned or shown |
| credential-protection.feature.md | User tokens are not stored when not needed |
| github-app-installation.feature.md | The user starts installation |
| github-app-installation.feature.md | A forged cross-site request to start installation is rejected |
| github-app-installation.feature.md | The user is still signed in when GitHub returns them after installation |
| github-app-installation.feature.md | The App requests only the approved minimum permissions |
| github-authentication.feature.md | Two simultaneous first sign-ins create one user |
| github-authentication.feature.md | The stored email follows the approved source order |
| github-authentication.feature.md | GitHub provides no display name |
| github-authentication.feature.md | Each authentication failure is explained safely |
| github-connection-status.feature.md | A visitor who is not signed in has no connection state |
| github-connection-status.feature.md | Suspended |
| github-connection-status.feature.md | Installation deleted |
| github-connection-status.feature.md | Verification failed |
| github-disconnection.feature.md | The user confirms disconnection |
| github-disconnection.feature.md | Repository access stops before GitHub confirms removal |
| github-disconnection.feature.md | Removing the installation at GitHub fails during disconnection |
| github-disconnection.feature.md | A user has one current connection after reconnecting |
| github-disconnection.feature.md | A suspended installation is not reconnected from DevPulse |
| github-profile.feature.md | The Profile handles a missing display name |
| github-profile.feature.md | The user chooses to refresh the profile |
| github-profile.feature.md | A refresh updates changed metadata |
| github-profile.feature.md | The user's identity stays stable when the username changes |
| github-profile.feature.md | The user cancels at GitHub during a refresh |
| github-profile.feature.md | GitHub denies authorization during a refresh |
| github-profile.feature.md | The refresh fails temporarily |
| github-profile.feature.md | A refresh authorized by a different GitHub account is rejected |
| github-profile.feature.md | A forged cross-site profile refresh is rejected |
| github-profile.feature.md | The Profile handles each loading and failure condition |
| github-profile.feature.md | Times are displayed in UTC and labelled as UTC |
| phase-02-acceptance.feature.md | A new user signs in and installs the GitHub App |
| phase-02-acceptance.feature.md | An authenticated user without an installation |
| phase-02-acceptance.feature.md | A suspended installation |
| phase-02-acceptance.feature.md | A deleted installation |
| tool-configuration.feature.md | The authorized repository count follows what GitHub provides |
| tool-configuration.feature.md | Opening Tool Configuration verifies the connection |
| tool-configuration.feature.md | The user requests re-verification |
| tool-configuration.feature.md | A successful retry leaves Verification failed |
| tool-configuration.feature.md | Restored permissions leave Permission attention required |
| tool-configuration.feature.md | An unsuspended installation leaves Suspended |
| tool-configuration.feature.md | A forged cross-site re-verification request is rejected |
| tool-configuration.feature.md | Tool Configuration handles each loading and failure condition |

## PRD alias index (PRD ID to Phase 2 ID)

PRD IDs stay in the Source column of `spec.md`. This index lists which Phase 2 requirements carry each PRD ID. Retired requirements are excluded.

| PRD ID | Phase 2 requirement ID(s) |
|---|---|
| FR-AUTH-001 | FR-AUTH-001 |
| FR-AUTH-002 | FR-AUTH-002, FR-AUTH-003 |
| FR-AUTH-003 | FR-SESS-001 |
| FR-AUTH-004 | FR-SESS-002 |
| FR-AUTH-005 | FR-ACC-001, FR-ACC-002, ER-ACC-001 |
| FR-AUTH-006 | FR-SESS-004 |
| FR-GH-001 | FR-INST-001 |
| FR-GH-002 | FR-INST-002 |
| FR-GH-003 | FR-INST-006, DR-CONN-003 |
| FR-GH-004 | DR-CONN-002, BR-005 |
| FR-GH-005 | FR-STAT-001, FR-STAT-009, FR-STAT-011, FR-STAT-012 |
| FR-GH-006 | FR-DISC-001 |
| FR-GH-007 | SR-PERM-001 |
| NFR-SEC-001 | SR-CRED-005, SR-CRED-006 |
| NFR-SEC-002 | SR-SESS-002 |
| NFR-SEC-003 | SR-STATE-001, SR-STATE-002, DR-STATE-001 |
| NFR-SEC-005 | SR-AUTHZ-001 |
| UX-004 | UI-A11Y-001 |

State mapping:

| PRD state (FR-GH-005) | Phase 2 state | Decision |
|---|---|---|
| Not connected | Authentication completed | R2-8 (DECIDED by owner, 2026-11-24) |
| Connected | Connected | n/a |
| Suspended | Suspended | n/a |
| Permission attention required | Permission attention required | n/a |
| Disconnected | Disconnected | n/a |
| Verification failed | Verification failed | n/a |
| (none) | Installation required | Phase 2 only |
| (none) | Installation deleted | Phase 2 only |

Note: PRD FR-AUTH-005 (protected resources) maps to both the backend rule (FR-ACC-001) and the frontend rule (FR-ACC-002).
