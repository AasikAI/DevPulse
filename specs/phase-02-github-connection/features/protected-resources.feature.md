# Protected resources: behaviour specification

```gherkin
Feature: Protected resources
  Protected backend interfaces and frontend routes are available only to signed-in users,
  and enforcement does not depend on the frontend.

  @FR-ACC-001 @critical
  Scenario: A signed-in user reaches a protected interface
    Given the user is signed in
    When the user requests their own protected information
    Then the request succeeds

  @FR-ACC-001 @ER-ACC-001 @security @critical
  Scenario: An unauthenticated request to a protected interface is rejected
    Given the requester has no session
    When the requester calls a protected interface directly, without using the DevPulse pages
    Then DevPulse answers that authentication is required
    And no protected data is returned
    And the answer does not reveal whether a session ever existed

  @FR-ACC-001 @ER-ACC-001 @ER-SESS-001 @ER-SESS-003 @ER-SESS-004 @security @blocked-by-OQ-001
  Scenario Outline: Missing, expired and revoked sessions are rejected
    Given the requester's session is <state>
    When the requester calls a protected interface
    Then DevPulse answers that authentication is required
    And no protected data is returned

    Examples:
      | state   |
      | missing |
      | expired |
      | revoked |

  @FR-ACC-002
  Scenario: A signed-in user opens a protected route
    Given the user is signed in
    When the user opens the Tool Configuration page
    Then the page is shown

  @FR-ACC-002 @critical
  Scenario: A visitor opening a protected route is sent to sign-in
    Given the visitor is not signed in
    When the visitor opens the Tool Configuration page
    Then the visitor is sent to the sign-in page
    And no protected content is shown

  @SR-AUTHZ-001 @security
  Scenario: A user cannot access another user's protected data
    Given two signed-in users exist
    When the first user requests data that belongs to the second user
    Then access is denied
    And none of the second user's data is returned

  @FR-ACC-003
  Scenario: The user returns to the page they first requested
    Given the visitor is not signed in
    And the visitor opened the Tool Configuration page and was sent to sign-in
    When the visitor signs in with GitHub
    Then the visitor is taken to the Tool Configuration page

  @SR-REDIR-001 @security
  Scenario Outline: Unsafe post-login destinations are ignored
    Given the visitor is sent to sign-in with the requested destination "<destination>"
    When the visitor signs in with GitHub
    Then the visitor is taken to the default signed-in page
    And the visitor is not sent to the requested destination

    Examples:
      | destination                  |
      | https://evil.example/phish   |
      | //evil.example/phish         |
      | javascript:alert(1)          |
      | /route-that-does-not-exist   |

  @UI-NAV-001
  Scenario: A visitor is not offered authenticated navigation
    Given the visitor is not signed in
    When the visitor views the application
    Then Profile, Tool Configuration and logout are not offered

  @ER-SYS-001 @UI-STATE-001
  Scenario: The backend is unavailable
    Given the DevPulse backend is unavailable
    When a signed-in user opens a page
    Then the page shows a safe unavailable state
    And the page does not present earlier protected content as current

  @UI-STATE-001
  Scenario: A page shows a loading state, then its content
    Given the user is signed in
    When a protected page is loading
    Then the page shows a loading state
    And then shows its content when the data arrives
```
