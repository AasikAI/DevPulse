# Credential protection: behaviour specification

```gherkin
Feature: Credential protection
  DevPulse never exposes, logs or carelessly stores credentials.

  @SR-CRED-005 @security @critical
  Scenario Outline: No token appears in what the browser receives
    Given the user is signed in and has a Connected GitHub installation
    When the interface requests <information>
    Then the response contains no GitHub token, installation token, private key or session credential

    Examples:
      | information            |
      | the current user       |
      | the profile            |
      | the Tool Configuration |
      | the connection status  |

  @SR-CRED-005 @security
  Scenario: No credential is kept in browser storage
    Given the user has signed in, used the application and logged out
    When the browser's local storage, session storage and script-readable cookies are inspected
    Then none of them contains a GitHub token, an installation token or a session credential

  @SR-CRED-001 @DR-SESS-001 @security
  Scenario: The raw session credential is never stored
    Given the user is signed in
    When the stored session data is inspected
    Then it contains a hash of the session credential
    And it does not contain the raw session credential

  @REV1 @SR-CRED-001 @security @blocked-by-design
  Scenario: Session credentials cannot be predicted
    Given sessions have been created for different sign-ins
    When the session credentials are compared
    Then no two session credentials are equal
    And no session credential can be derived from the user, the sign-in time or another session's credential

  @SR-CRED-002 @security
  Scenario: The private key is not in normal database tables
    When all normal PostgreSQL application data is inspected
    Then the GitHub App private key does not appear in it
    And the private key is not present in the repository

  @REV1 @SR-CRED-002 @SR-CRED-005 @security
  Scenario Outline: The private key is never returned or shown
    When <surface> is produced
    Then it does not contain the GitHub App private key

    Examples:
      | surface                                  |
      | the current-user response                |
      | the profile response                     |
      | the Tool Configuration response          |
      | the connection-status response           |
      | the sign-in page and its failure message |
      | an installation-verification error       |
      | a profile-refresh error                  |
      | a disconnection error                    |

  @SR-CRED-006 @security
  Scenario: Logs contain no secrets
    Given the user signs in, installs the App, refreshes the profile, disconnects and logs out
    When the application logs for these actions are inspected
    Then they contain no token, authorization header, cookie, secret or private key

  @SR-CRED-005 @SR-ERR-001 @security
  Scenario Outline: Errors and URLs contain no credential
    When <failure> occurs
    Then the visible error message contains no credential, stack trace or raw GitHub error content
    And no URL or query parameter in the flow contains a credential

    Examples:
      | failure                              |
      | an authentication failure            |
      | an installation verification failure |
      | a profile refresh failure            |
      | a disconnection failure              |

  @SR-CRED-003 @security
  Scenario: Installation access is short-lived
    Given DevPulse needs to read installation information from GitHub
    When DevPulse obtains an installation access token
    Then the token is short-lived
    And the token is not treated as a permanent credential
    And the token is not stored for later reuse

  @REV1 @SR-CRED-004 @security
  Scenario: User tokens are not stored when not needed
    Given the user has signed in and refreshed their profile through GitHub authorization
    When the stored data is inspected
    Then no GitHub user access token is stored
    And no GitHub user refresh token is stored

  @SR-STATE-001 @SR-STATE-002 @DR-STATE-001 @security
  Scenario: Replayed callbacks are rejected
    Given a sign-in callback and an installation callback were each processed once
    When each callback is replayed
    Then both replays are rejected
    And no session or installation record is created by either replay
```
