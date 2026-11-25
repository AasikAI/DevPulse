# GitHub authentication: behaviour specification

```gherkin
Feature: GitHub authentication
  A visitor continues with GitHub so DevPulse can recognise them by their GitHub identity,
  without a separate password.

  Background:
    Given DevPulse offers sign-in with GitHub
    And the visitor is not signed in to DevPulse

  @FR-AUTH-001 @UI-AUTH-001 @critical
  Scenario: Visitor starts GitHub authorization
    When the visitor chooses "Continue with GitHub"
    Then the visitor is taken to GitHub to authorize DevPulse
    And no DevPulse session exists yet

  @UI-AUTH-001
  Scenario: Sign-in offers GitHub only
    When the visitor opens the sign-in page
    Then the page offers "Continue with GitHub"
    And the page shows no email field
    And the page shows no password field

  @FR-AUTH-002 @FR-AUTH-005 @FR-SESS-001 @DR-USER-001 @BR-001 @critical
  Scenario: A new user authenticates
    Given the GitHub account with ID 1001 has never signed in to DevPulse
    When the visitor authorizes DevPulse on GitHub as that account
    Then a DevPulse user exists for GitHub account ID 1001
    And the user is signed in to DevPulse
    And the user's last login time is the time of this sign-in

  @FR-AUTH-002 @FR-AUTH-005 @DR-USER-001 @BR-001
  Scenario: An existing user authenticates again without creating a duplicate
    Given a DevPulse user exists for GitHub account ID 1001
    When the visitor authorizes DevPulse on GitHub as account ID 1001
    Then the visitor is signed in as the existing user
    And exactly one DevPulse user exists for GitHub account ID 1001
    And the user's last login time is updated

  @REV1 @FR-AUTH-006 @DR-USER-001 @BR-001 @critical
  Scenario: Two simultaneous first sign-ins create one user
    Given the GitHub account with ID 1001 has never signed in to DevPulse
    When two sign-ins for GitHub account ID 1001 complete at the same time
    Then exactly one DevPulse user exists for GitHub account ID 1001
    And both sign-ins are signed in as that user

  @FR-AUTH-003 @DR-USER-002
  Scenario Outline: Changed GitHub profile data updates the existing user
    Given a DevPulse user exists for GitHub account ID 1001 with <field> "<old>"
    When the visitor authorizes DevPulse on GitHub as account ID 1001 with <field> "<new>"
    Then exactly one DevPulse user exists for GitHub account ID 1001
    And that user's <field> is "<new>"

    Examples:
      | field        | old                    | new                    |
      | username     | old-handle             | new-handle             |
      | display name | Old Name               | New Name               |
      | avatar       | https://example/a1.png | https://example/a2.png |
      | email        | old@example.test       | new@example.test       |

  @FR-AUTH-004 @BR-008
  Scenario: GitHub provides no email
    Given the GitHub account with ID 1002 has no email available to DevPulse
    When the visitor authorizes DevPulse on GitHub as that account
    Then the user is signed in to DevPulse
    And the user has no stored email
    And DevPulse has not invented an email for the user

  @REV1 @FR-PROF-007 @DR-USER-002 @BR-008
  Scenario Outline: The stored email follows the approved source order
    Given the GitHub account with ID 1004 makes <primary> as its primary verified email available to DevPulse
    And the account makes <public> as its public email available to DevPulse
    When the visitor authorizes DevPulse on GitHub as that account
    Then the user's stored email is <stored>

    Examples:
      | primary           | public            | stored            |
      | "p@example.test"  | "q@example.test"  | "p@example.test"  |
      | no email          | "q@example.test"  | "q@example.test"  |
      | no email          | no email          | no email          |

  @REV1 @FR-PROF-006 @DR-USER-002
  Scenario: GitHub provides no display name
    Given the GitHub account with ID 1003 has no display name available to DevPulse
    When the visitor authorizes DevPulse on GitHub as that account
    Then the user is signed in to DevPulse
    And the user has no stored display name
    And DevPulse has not used the username as a display name

  @ER-AUTH-001
  Scenario: The visitor cancels at GitHub
    When the visitor starts GitHub authorization
    And the visitor cancels on the GitHub authorization page
    Then the visitor is not signed in
    And the visitor sees a safe message and can try again

  @ER-AUTH-002
  Scenario: GitHub denies authorization
    When GitHub returns an access-denied result to DevPulse
    Then no DevPulse session is created
    And the visitor sees a safe explanation

  @ER-AUTH-003 @SR-STATE-001 @security
  Scenario: The callback has no authorization code
    When DevPulse receives an authorization callback without an authorization code
    Then the callback is rejected
    And no DevPulse session is created

  @ER-AUTH-004 @SR-STATE-001 @security
  Scenario: The callback has no state value
    When DevPulse receives an authorization callback without a state value
    Then the callback is rejected
    And no DevPulse session is created

  @ER-AUTH-005 @SR-STATE-001 @security
  Scenario: The callback has an unknown state value
    When DevPulse receives an authorization callback with a state value it never issued
    Then the callback is rejected
    And no DevPulse session is created

  @ER-AUTH-006 @SR-STATE-001 @DR-STATE-001 @security @blocked-by-OQ-012
  Scenario: The callback has an expired state value
    Given the visitor started GitHub authorization
    And the state value's lifetime has elapsed
    When GitHub returns the visitor to DevPulse with that state value
    Then the callback is rejected
    And no DevPulse session is created

  @ER-AUTH-007 @SR-STATE-001 @DR-STATE-001 @security
  Scenario: The callback reuses a state value
    Given the visitor completed GitHub authorization with a state value
    When the same callback is submitted again
    Then the second callback is rejected
    And no additional session is created

  @ER-AUTH-008 @SR-STATE-001 @security
  Scenario: The state value belongs to a different browser
    Given one browser started GitHub authorization
    When a different browser submits the callback with that state value
    Then the callback is rejected
    And no DevPulse session is created

  @ER-AUTH-009
  Scenario: GitHub is temporarily unavailable during authentication
    Given GitHub is temporarily unavailable
    When the visitor completes authorization on GitHub
    Then no DevPulse session is created
    And the visitor sees a retryable message
    And existing DevPulse users are unchanged

  @ER-SYS-002
  Scenario: GitHub rate-limits authentication
    Given GitHub is rate-limiting DevPulse
    When the visitor completes authorization on GitHub
    Then the visitor sees a safe retry-later message
    And no stored user data is changed

  @REV1 @UI-AUTH-002 @SR-ERR-001 @blocked-by-OQ-012
  Scenario Outline: Each authentication failure is explained safely
    Given the visitor started GitHub authorization
    When <failure>
    Then the sign-in page tells the visitor what happened in plain language
    And the page offers "Continue with GitHub" again
    And the message contains no stack trace, token or raw GitHub error content

    Examples:
      | failure                                                                 |
      | the visitor cancels on the GitHub authorization page                    |
      | GitHub returns an access-denied result                                  |
      | the callback arrives without an authorization code                      |
      | the callback arrives without a state value                              |
      | the callback arrives with a state value DevPulse never issued           |
      | the callback arrives with an expired state value                        |
      | the callback arrives with a state value that was already used           |
      | the callback arrives from a browser that did not start authorization    |
      | GitHub is temporarily unavailable                                       |
      | GitHub is rate-limiting DevPulse                                        |
```
