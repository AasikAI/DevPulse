# GitHub disconnection: behaviour specification

```gherkin
Feature: GitHub disconnection
  A user can disconnect GitHub without being logged out of DevPulse, and can reconnect later.

  Background:
    Given the user is signed in as GitHub account ID 1001
    And the user has a Connected GitHub installation

  @FR-DISC-001
  Scenario: The user requests disconnection
    When the user chooses "Disconnect"
    Then DevPulse asks the user to confirm

  @FR-DISC-002
  Scenario: The user is asked to confirm
    When the user chooses "Disconnect"
    Then the confirmation explains that repository access will stop
    And the user can confirm or cancel using the keyboard

  @FR-DISC-002
  Scenario: The user cancels disconnection
    Given the user chose "Disconnect"
    When the user cancels the confirmation
    Then the connection state is still Connected
    And nothing is changed

  @REV1 @FR-DISC-003 @DR-CONN-004 @DR-CONN-001 @critical
  Scenario: The user confirms disconnection
    Given the user chose "Disconnect"
    When the user confirms
    Then the connection state is Disconnected
    And the disconnection time is recorded
    And the connection remains on record
    And DevPulse asks GitHub to remove the installation

  @REV1 @FR-DISC-003 @BR-002
  Scenario: Repository access stops before GitHub confirms removal
    Given the user chose "Disconnect"
    And GitHub has not yet confirmed removal of the installation
    When the user confirms
    Then the connection state is Disconnected
    And repository access is not available

  @BR-004 @critical
  Scenario: The DevPulse session is preserved
    Given the user chose "Disconnect"
    When the user confirms
    Then the user is still signed in to DevPulse
    And the user can still open the Profile

  @FR-DISC-003
  Scenario: Future repository access is prevented
    Given the user has disconnected GitHub
    When any later feature asks for repository access for the user
    Then repository access is not available

  @FR-DISC-004
  Scenario: Disconnecting twice is safe
    Given the user has disconnected GitHub
    When the user requests disconnection again
    Then the request completes without error
    And the connection is unchanged
    And the disconnection time is not overwritten

  @REV1 @ER-DISC-001 @SR-ERR-001
  Scenario: Removing the installation at GitHub fails during disconnection
    Given GitHub fails to remove the installation
    When the user confirms disconnection
    Then the connection state is Disconnected
    And the connection is marked removal pending
    And the user is shown safe instructions to remove the App on GitHub
    And no credential or raw GitHub error is shown

  @ER-DISC-002
  Scenario: The installation is already removed at GitHub
    Given the installation was already removed at GitHub
    When the user confirms disconnection
    Then disconnection completes
    And the connection state is Disconnected

  @SR-AUTHZ-001 @security
  Scenario: A user cannot disconnect another user's connection
    Given a second user has a Connected GitHub installation
    When the first user asks to disconnect the second user's connection
    Then access is denied
    And the second user's connection is unchanged

  @SR-CSRF-001 @security @blocked-by-OQ-013
  Scenario: A forged cross-site disconnection is rejected
    When another website submits a disconnection request using the user's session cookie
    Then the request is rejected
    And the connection state is still Connected

  @REV2 @FR-DISC-005 @DR-CONN-005
  Scenario: The user reconnects after disconnecting
    Given the user has disconnected GitHub
    When the user chooses "Reconnect"
    Then the user is taken through installation again
    And the connection state is Installation required until the installation is verified
    And, when a new installation ID is verified, the earlier connection remains on record as history

  @REV2 @FR-DISC-005 @DR-CONN-005
  Scenario: The user reconnects after the installation was deleted
    Given the connection state is Installation deleted
    When the user chooses "Reconnect"
    Then the user is taken through installation again
    And the connection state is Installation required until the installation is verified
    And, when a new installation ID is verified, the earlier connection remains on record as history

  @REV1 @DR-CONN-005 @FR-INST-005
  Scenario: A user has one current connection after reconnecting
    Given the user has a Disconnected connection for installation ID 5001
    When the user reconnects and a new installation ID 5002 is verified
    Then the user has exactly one current connection, for installation ID 5002
    And the earlier connection for installation ID 5001 remains on record as history

  @REV1 @FR-DISC-006 @FR-STAT-009 @FR-INST-008
  Scenario: A suspended installation is not reconnected from DevPulse
    Given the connection state is Suspended
    When the user opens Tool Configuration
    Then the page does not offer "Reconnect"
    And the page offers "Manage installation"
    And choosing "Manage installation" takes the user to GitHub's page for managing the installation
```
