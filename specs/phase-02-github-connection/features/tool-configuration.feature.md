# Tool Configuration: behaviour specification

```gherkin
Feature: Tool Configuration
  Tool Configuration is where the user configures and manages their GitHub connection.
  DevPulse learns of GitHub-side changes only when it verifies the connection.

  Background:
    Given the user is signed in as GitHub account ID 1001

  @REV2 @FR-CONF-001 @FR-STAT-005
  Scenario: Before installation
    Given the user has no current connection and has never started installation or reconnection
    When the user opens Tool Configuration
    Then GitHub is shown as a provider
    And the connection state is Authentication completed
    And the page offers to install the DevPulse GitHub App

  @FR-CONF-001 @FR-CONF-002
  Scenario: After installation
    Given the user has a Connected GitHub installation
    When the user opens Tool Configuration
    Then GitHub is shown as a configured provider
    And the connection state is Connected

  @FR-CONF-002
  Scenario: Provider and account details are shown
    Given the user has a Connected GitHub installation
    When the user opens Tool Configuration
    Then the page shows the provider name and the connected GitHub user
    And the page shows the installation account and its account type
    And the page shows the DevPulse authentication status and the GitHub installation status
    And the page shows the configuration status and the last verification time

  @FR-CONF-002 @FR-INST-002
  Scenario Outline: The repository-authorization mode is shown
    Given the user has a Connected installation with mode "<mode>"
    When the user opens Tool Configuration
    Then the page shows the repository-authorization mode "<mode>"

    Examples:
      | mode                  |
      | All repositories      |
      | Selected repositories |

  @REV1 @FR-CONF-002
  Scenario Outline: The authorized repository count follows what GitHub provides
    Given the user has a Connected installation with selected repositories
    And GitHub <availability> the number of authorized repositories
    When the user opens Tool Configuration
    Then the page <display>

    Examples:
      | availability   | display                                              |
      | provides       | shows the number of authorized repositories           |
      | does not provide | shows no repository count and invents none          |

  @FR-STAT-003
  Scenario: The permission status is shown
    Given the user has a Connected GitHub installation
    When the user opens Tool Configuration
    Then the page shows the permission status
    And the status compares the granted permissions with the required permissions

  @REV2 @FR-CONF-004 @FR-INST-001 @FR-INST-008 @FR-INST-009 @FR-DISC-001 @FR-DISC-005 @FR-DISC-006 @FR-CONF-005 @FR-STAT-011
  Scenario Outline: Each state offers exactly its own actions
    Given the connection state is <state>
    When the user opens Tool Configuration
    Then the page offers exactly these actions: <offered>
    And the page does not offer: <not_offered>

    Examples:
      | state                         | offered                                      | not_offered                                                          |
      | Authentication completed      | Install the DevPulse GitHub App              | Manage installation, Re-verify, Disconnect, Reconnect                |
      | Installation required         | Install the DevPulse GitHub App              | Manage installation, Re-verify, Disconnect, Reconnect                |
      | Connected                     | Manage installation, Re-verify, Disconnect   | Install the DevPulse GitHub App, Reconnect                           |
      | Permission attention required | Manage installation, Re-verify, Disconnect   | Install the DevPulse GitHub App, Reconnect                           |
      | Suspended                     | Manage installation, Re-verify, Disconnect   | Install the DevPulse GitHub App, Reconnect                           |
      | Installation deleted          | Reconnect                                    | Install the DevPulse GitHub App, Manage installation, Re-verify, Disconnect |
      | Verification failed           | Retry verification, Manage installation, Disconnect | Install the DevPulse GitHub App, Reconnect                  |
      | Disconnected                  | Reconnect                                    | Install the DevPulse GitHub App, Manage installation, Re-verify, Disconnect |

  @REV1 @FR-CONF-006 @critical
  Scenario: Opening Tool Configuration verifies the connection
    Given the user has a Connected GitHub installation
    When the user opens Tool Configuration
    Then DevPulse verifies the connection with GitHub
    And the last verification time shown is the time of this verification

  @REV2 @FR-CONF-006
  Scenario: Each opening of Tool Configuration verifies the connection
    Given the user opened Tool Configuration and left it
    When the user opens Tool Configuration again shortly afterwards
    Then DevPulse verifies the connection with GitHub again
    And the last verification time shown is the time of this latest verification

  @REV1 @FR-CONF-005
  Scenario: The user requests re-verification
    Given the user has a connection in the state Connected
    When the user chooses "Re-verify"
    Then DevPulse verifies the connection with GitHub
    And the last verification time shown is the time of this verification
    And the connection state shown is the state that verification found

  @REV1 @FR-STAT-011 @FR-CONF-005 @critical
  Scenario: A successful retry leaves Verification failed
    Given the connection state is Verification failed
    When the user chooses "Retry verification"
    And verification now confirms the installation with the required permissions
    Then the connection state is Connected
    And repository access is available

  @REV1 @FR-STAT-008 @FR-CONF-005
  Scenario: Restored permissions leave Permission attention required
    Given the connection state is Permission attention required
    And the missing permissions have been restored on GitHub
    When the user chooses "Re-verify"
    Then the connection state is Connected
    And repository access is available

  @REV1 @FR-STAT-009 @FR-CONF-005
  Scenario: An unsuspended installation leaves Suspended
    Given the connection state is Suspended
    And the installation has been unsuspended on GitHub
    When the user chooses "Re-verify"
    Then the connection state is Connected
    And repository access is available

  @REV2 @ER-CONF-001
  Scenario: GitHub is temporarily unavailable while verifying
    Given the user has a Connected GitHub installation
    And GitHub is temporarily unavailable
    When the user opens Tool Configuration
    Then the page keeps showing the last known state
    And the page shows the last verification time
    And the page offers a retry
    And the page shows a visible notice that the connection could not be verified now

  @REV1 @SR-CSRF-001 @security @blocked-by-OQ-013
  Scenario: A forged cross-site re-verification request is rejected
    Given the user has a Connected GitHub installation
    When another website submits a re-verification request using the user's session cookie
    Then the request is rejected
    And the last verification time is unchanged

  @UI-CONF-001 @BR-006
  Scenario Outline: Tool Configuration has no synchronization controls
    Given the connection state is <state>
    When the user opens Tool Configuration
    Then the page shows no synchronization control
    And the page shows no synchronization status

    Examples:
      | state                         |
      | Authentication completed      |
      | Installation required         |
      | Connected                     |
      | Permission attention required |
      | Suspended                     |
      | Installation deleted          |
      | Verification failed           |
      | Disconnected                  |

  @SR-AUTHZ-001 @security
  Scenario: Each user sees only their own configuration
    Given a second user has a Connected GitHub installation
    When the first user opens Tool Configuration
    Then the page shows only the first user's configuration
    And no detail of the second user's installation is shown

  @FR-CONF-003 @DR-CONF-001
  Scenario: The configuration survives logout and login
    Given the user has a Connected GitHub installation
    When the user logs out and signs in again
    Then Tool Configuration still shows the same connection as Connected

  @UI-CONF-002
  Scenario: Status is never conveyed by colour alone
    Given the user has a connection in any state
    When the user opens Tool Configuration
    Then every status is shown as text

  @UI-A11Y-001
  Scenario: Tool Configuration can be used by keyboard
    When the user navigates Tool Configuration using only the keyboard
    Then every control can be reached and operated
    And each control has visible focus and an accessible name

  @REV1 @UI-STATE-001 @ER-SYS-001
  Scenario Outline: Tool Configuration handles each loading and failure condition
    When <condition>
    Then Tool Configuration shows <outcome>

    Examples:
      | condition                           | outcome                                 |
      | Tool Configuration is loading       | a loading state                         |
      | Tool Configuration fails to load    | a recoverable error with a retry action |
      | the DevPulse backend is unavailable | a safe unavailable state                |
```
