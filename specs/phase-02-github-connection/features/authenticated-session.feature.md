# Authenticated session: behaviour specification

```gherkin
Feature: Authenticated session
  A signed-in user keeps a protected DevPulse session that survives refreshes, can expire
  or be revoked, and ends when the user logs out.

  Background:
    Given a DevPulse user exists for GitHub account ID 1001

  @FR-SESS-001 @SR-SESS-002 @DR-SESS-001 @critical
  Scenario: A session is created securely at sign-in
    When the user signs in with GitHub
    Then the browser receives a session cookie that page scripts cannot read
    And the session has an owner, a creation time, an expiry time and is not revoked

  @FR-SESS-002 @critical
  Scenario: The session is restored after a browser refresh
    Given the user is signed in
    When the user refreshes the browser
    Then the user is still signed in
    And the user is not asked to authenticate again

  @FR-SESS-003
  Scenario: The interface retrieves the current user
    Given the user is signed in
    When the interface asks who the current user is
    Then DevPulse returns that user's identity and profile summary
    And the response contains no credential

  @ER-SESS-001
  Scenario: A request has no session
    When a request arrives with no session cookie
    Then DevPulse treats the requester as unauthenticated

  @ER-SESS-002 @security
  Scenario: A request has a malformed or unrecognised session credential
    When a request arrives with a session credential DevPulse never issued
    Then DevPulse treats the requester as unauthenticated

  @ER-SESS-003 @FR-SESS-006 @blocked-by-OQ-001
  Scenario: A request has an expired session
    Given the user is signed in
    And the session lifetime has elapsed
    When the user makes a request
    Then DevPulse treats the requester as unauthenticated
    And the expired session is never accepted

  @ER-SESS-004
  Scenario: A request has a revoked session
    Given the user is signed in
    And the session has been revoked
    When the user makes a request
    Then DevPulse treats the requester as unauthenticated

  @FR-SESS-004 @critical
  Scenario: The user logs out
    Given the user is signed in
    When the user logs out
    Then the session is revoked
    And later requests with that session are treated as unauthenticated

  @FR-SESS-005
  Scenario Outline: Logging out is idempotent
    Given the user's session is <state>
    When the user logs out
    Then logout completes without error
    And the user is unauthenticated

    Examples:
      | state   |
      | revoked |
      | expired |
      | absent  |

  @REV1 @FR-SESS-008
  Scenario: A user can be signed in on two browsers at once
    Given the user signs in on a first browser
    When the user also signs in on a second browser
    Then both sessions are accepted
    And both browsers show the user as signed in

  @REV1 @FR-SESS-008 @FR-SESS-004 @critical
  Scenario: Logout ends only the current session
    Given the user is signed in on a first browser and on a second browser
    When the user logs out on the first browser
    Then the first browser's session is revoked
    And the second browser's session is still accepted

  @BR-003 @critical
  Scenario: Logout leaves the GitHub installation in place
    Given the user has a Connected GitHub installation
    When the user logs out
    Then the GitHub installation is unchanged
    And the connection is still Connected when the user signs in again

  @SR-SESS-001 @security
  Scenario: Signing in issues a new session credential
    Given a visitor holds a session credential from before signing in
    When the visitor signs in with GitHub
    Then DevPulse issues a new session credential
    And the credential held before signing in is not accepted

  @SR-SESS-002 @security @blocked-by-OQ-003 @blocked-by-OQ-001
  Scenario Outline: Cookie security in production
    Given DevPulse runs in production
    When a session cookie is issued
    Then the cookie is <property>

    Examples:
      | property                                |
      | HTTP-only                               |
      | Secure                                  |
      | limited by an expiry time               |
      | subject to the approved SameSite policy |

  @SR-CSRF-001 @security @blocked-by-OQ-013
  Scenario: A forged cross-site logout is rejected
    Given the user is signed in
    When another website submits a logout request using the user's session cookie
    Then the request is rejected
    And the session remains active

  @FR-SESS-007 @blocked-by-OQ-004
  Scenario: Expired and revoked sessions are cleaned up
    Given sessions exist that are expired or revoked
    When the approved cleanup strategy runs
    Then those sessions are removed or retired
    And active sessions are unaffected
```
