# GitHub connection status: behaviour specification

```gherkin
Feature: GitHub connection status
  A signed-in user has exactly one of eight connection states. DevPulse learns of changes made
  on GitHub only when it verifies the connection. DevPulse authentication stays separate from
  GitHub installation, and repository access is available only in Connected.

  @REV1 @FR-STAT-001
  Scenario: A visitor who is not signed in has no connection state
    Given the visitor is not signed in
    When the visitor views the application
    Then no connection state is shown

  @REV2 @FR-STAT-005 @FR-STAT-001
  Scenario: Authentication completed
    Given the user is signed in
    And the user has no current connection and has never started installation or reconnection
    When the user views the connection status
    Then the connection state is Authentication completed
    And repository access is not available

  @REV2 @FR-STAT-006 @FR-STAT-001
  Scenario Outline: Installation required
    Given the user is signed in
    And the user has started installation, or reconnection, and <situation>
    When the user views the connection status
    Then the connection state is Installation required
    And repository access is not available

    Examples:
      | situation                 |
      | has not completed it      |
      | cancelled at GitHub       |
      | verification has not completed |

  @REV2 @FR-STAT-006 @FR-STAT-005
  Scenario: Installation required does not expire
    Given the user started installation and did not complete it
    When a long time passes with no further action by the user
    Then the connection state is still Installation required
    And the connection state has not returned to Authentication completed

  @FR-STAT-007 @FR-STAT-001 @BR-002
  Scenario: Connected
    Given the user is signed in
    And the user has a verified, active installation with the required permissions
    When the user views the connection status
    Then the connection state is Connected
    And repository access is available

  @REV2 @FR-STAT-008 @FR-STAT-003
  Scenario: Permission attention required
    Given the user has a Connected installation
    And the permissions granted to the installation now differ from the required permissions
    When DevPulse verifies the connection and finds the difference
    Then the connection state is Permission attention required
    And the permissions that need attention are named

  @REV1 @FR-STAT-009 @BR-002
  Scenario: Suspended
    Given the user has a Connected installation
    And GitHub has suspended the installation
    When DevPulse verifies the connection and GitHub reports the installation as suspended
    Then the connection state is Suspended
    And repository access is not available

  @REV1 @FR-STAT-010 @BR-002
  Scenario: Installation deleted
    Given the user has a Connected installation
    And the installation has been removed on GitHub
    When DevPulse verifies the connection and GitHub reports that the installation no longer exists
    Then the connection state is Installation deleted
    And repository access is not available

  @REV1 @FR-STAT-011 @BR-002
  Scenario: Verification failed
    Given the user has a connection
    When DevPulse verifies the connection and cannot confirm the installation for a reason that is not temporary
    Then the connection state is Verification failed
    And repository access is not available
    And "Retry verification" is offered

  @FR-STAT-012 @BR-002
  Scenario: Disconnected
    Given the user has disconnected GitHub
    When the user views the connection status
    Then the connection state is Disconnected
    And repository access is not available

  @REV2 @FR-STAT-002 @BR-002 @blocked-by-OQ-028
  Scenario Outline: Authentication and installation are separate indicators
    Given the user's DevPulse authentication is "signed in" and the GitHub installation is "<installed>"
    When the status is shown
    Then DevPulse authentication shows "signed in" as its own indicator
    And the GitHub installation shows "<installed>" as its own indicator
    And repository access is "<access>"

    Examples:
      | installed             | access      |
      | not installed         | unavailable |
      | active                | available   |
      | suspended             | unavailable |
      | removed at GitHub     | unavailable |
      | disconnected          | unavailable |

  @REV2 @BR-002 @FR-STAT-001
  Scenario Outline: Repository access is available when Connected and unavailable in the other specified states
    Given the connection state is <state>
    When the user views the connection status
    Then repository access is <access>

    Examples:
      | state                    | access      |
      | Authentication completed | unavailable |
      | Installation required    | unavailable |
      | Connected                | available   |
      | Suspended                | unavailable |
      | Installation deleted     | unavailable |
      | Verification failed      | unavailable |
      | Disconnected             | unavailable |

  @FR-STAT-001
  Scenario: A user has exactly one state at a time
    Given the user has any connection
    When the user views the connection status
    Then exactly one connection state is shown

  @SR-AUTHZ-001 @security
  Scenario: Connection status is private to its owner
    Given a second user has a Suspended installation
    When the first user views their connection status
    Then the first user's status is unaffected
    And no detail of the second user's connection is shown
```
