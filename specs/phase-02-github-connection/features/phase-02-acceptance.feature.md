# Phase 2 acceptance: behaviour specification

```gherkin
Feature: Phase 2 acceptance
  End-to-end behaviour that shows GitHub authentication and connection works as a whole.

  @REV1 @FR-AUTH-001 @FR-AUTH-002 @FR-INST-001 @FR-INST-005 @FR-INST-006 @FR-STAT-005 @FR-STAT-007 @BR-002 @critical @blocked-by-OQ-005
  Scenario: A new user signs in and installs the GitHub App
    Given a visitor who has never used DevPulse
    When the visitor continues with GitHub and authorizes DevPulse
    Then the visitor is signed in and the connection state is Authentication completed
    When the user installs the DevPulse GitHub App on their personal account
    And DevPulse verifies the installation
    Then the connection state is Connected
    And the installation is owned by this user
    And DevPulse authentication and GitHub installation are shown as separate indicators

  @FR-AUTH-002 @FR-CONF-003 @FR-SESS-002 @critical
  Scenario: A returning user with an installation
    Given a user with a Connected GitHub installation has logged out
    When the user continues with GitHub again
    Then the user is signed in as the same DevPulse user
    And Tool Configuration still shows the connection as Connected
    And refreshing the browser keeps the user signed in

  @REV1 @FR-STAT-005 @FR-STAT-001
  Scenario: An authenticated user without an installation
    Given a user who has signed in and not installed the App
    When the user opens Tool Configuration
    Then the connection state is Authentication completed
    And the page offers to install the DevPulse GitHub App
    And repository access is not available

  @FR-AUTH-004 @FR-PROF-003 @BR-008
  Scenario: A user whose GitHub account provides no email
    Given the GitHub account provides no email
    When the visitor continues with GitHub and authorizes DevPulse
    Then the user is signed in
    And the Profile shows "Email not available from GitHub"

  @BR-003 @FR-SESS-004 @critical
  Scenario: Logout preserves the installation
    Given a signed-in user with a Connected GitHub installation
    When the user logs out
    Then the user is signed out
    And the GitHub installation is unchanged

  @BR-004 @FR-DISC-003 @critical
  Scenario: Disconnection preserves the DevPulse session
    Given a signed-in user with a Connected GitHub installation
    When the user confirms disconnection
    Then the connection state is Disconnected
    And the user is still signed in

  @REV1 @FR-STAT-009 @FR-CONF-006
  Scenario: A suspended installation
    Given a signed-in user with a Connected GitHub installation
    And GitHub has suspended the installation
    When DevPulse verifies the connection and GitHub reports the installation as suspended
    Then the connection state is Suspended
    And the user can still use the Profile
    And repository access is not available

  @REV1 @FR-STAT-010 @FR-DISC-005 @FR-CONF-006
  Scenario: A deleted installation
    Given a signed-in user with a Connected GitHub installation
    And the installation has been removed on GitHub
    When DevPulse verifies the connection and GitHub reports that the installation no longer exists
    Then the connection state is Installation deleted
    And the page offers "Reconnect"
    And repository access is not available

  @REV2 @FR-STAT-008 @FR-CONF-006
  Scenario: A permission change needs attention
    Given a signed-in user with a Connected GitHub installation
    And the permissions granted to the installation no longer match the required permissions
    When DevPulse verifies the connection and finds the difference
    Then the connection state is Permission attention required

  @BR-006 @UI-CONF-001 @critical
  Scenario: Phase 2 performs no repository-activity synchronization
    Given a signed-in user with a Connected GitHub installation
    When the user uses every Phase 2 page
    Then no commits, pull requests, reviews, issues, languages, workflows or workflow runs are retrieved or stored
    And no page offers a synchronization control or shows a synchronization status

  @BR-007
  Scenario: DevPulse uses neutral language
    When the user reads the Profile and Tool Configuration
    Then no text presents any value as a measure of productivity, performance or skill
```
