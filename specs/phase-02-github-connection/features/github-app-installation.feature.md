# GitHub App installation: behaviour specification

```gherkin
Feature: GitHub App installation
  A signed-in user installs the DevPulse GitHub App on their personal account, and DevPulse
  verifies the installation before treating it as active.

  Background:
    Given the user is signed in as GitHub account ID 1001

  @REV1 @FR-INST-001 @critical @blocked-by-OQ-005
  Scenario: The user starts installation
    When the user chooses to install the DevPulse GitHub App
    Then the user is taken to GitHub to install the App
    And the connection state is Installation required

  @REV1 @SR-CSRF-001 @security @blocked-by-OQ-013
  Scenario: A forged cross-site request to start installation is rejected
    When another website submits a request to start installation using the user's session cookie
    Then the request is rejected
    And no installation attempt is started
    And the connection state is unchanged

  @FR-INST-003 @DR-CONN-001
  Scenario: The user installs on their personal account
    When the user installs the App on their personal GitHub account
    Then the installation is recorded with account type "User"

  @FR-INST-002
  Scenario: The user grants all repositories
    When the user installs the App and grants access to all repositories
    Then the connection shows the repository-authorization mode "All repositories"

  @FR-INST-002
  Scenario: The user grants selected repositories
    When the user installs the App and grants access to selected repositories
    Then the connection shows the repository-authorization mode "Selected repositories"
    And the authorized repository count is shown when GitHub provides it

  @REV2 @ER-INST-006 @FR-STAT-006
  Scenario: The user cancels installation at GitHub
    Given the user started installation
    When the user cancels on GitHub
    Then no connection is created
    And the user is still signed in
    And the connection state is still Installation required

  @FR-INST-009 @FR-STAT-006
  Scenario: The user restarts installation while it is required
    Given the connection state is Installation required
    When the user chooses to install the DevPulse GitHub App again
    Then the user is taken to GitHub to install the App

  # RETIRED (Installation required does not expire, revision 2). Kept in place for the record.
  @RETIRED @REV2 @FR-STAT-013 @FR-STAT-005
  Scenario: An installation attempt expires without completion
    Given the user started installation and did not complete it
    When the installation attempt's lifetime elapses
    Then the connection state returns to Authentication completed
    And the user is offered the installation action again

  @REV2 @ER-INST-008 @FR-STAT-006 @security
  Scenario: An installation callback reports an organisation account
    Given the connection state is Installation required
    When GitHub returns the user to DevPulse after an installation on an organisation account
    Then the callback is rejected
    And the user sees a safe message that only personal GitHub accounts are supported in Phase 2
    And no connection is created
    # [INFERRED] consequence of the owner's decision: the installation was not completed, so the state is unchanged
    And the connection state is still Installation required

  @REV2 @SR-STATE-002 @DR-STATE-001 @FR-STAT-006 @blocked-by-OQ-024
  Scenario: The user returns to GitHub's installation flow after the correlation value has expired
    Given the connection state is Installation required
    And the correlation value for the installation has expired
    When GitHub returns the user to DevPulse
    Then the outcome follows the approved decision
    And the connection state is not changed by this return alone

  @FR-INST-005 @FR-INST-006 @DR-CONN-001 @DR-CONN-003 @DR-CONF-001 @SR-STATE-002 @BR-002 @critical @blocked-by-OQ-017 @blocked-by-OQ-005
  Scenario: A successful installation callback is verified and recorded
    Given the user started installation
    When GitHub returns the user to DevPulse after a successful installation
    Then DevPulse verifies the installation with GitHub
    And the installation is recorded as owned by the signed-in user
    And the stored connection includes its installation ID, account, account type, repository-selection mode and granted permissions
    And the connection state is Connected
    And repository access is available

  @REV1 @FR-SESS-002 @FR-INST-006 @blocked-by-OQ-003
  Scenario: The user is still signed in when GitHub returns them after installation
    Given the user started installation
    When GitHub returns the user to DevPulse after a successful installation
    Then the user is still signed in as GitHub account ID 1001

  @ER-INST-001 @security
  Scenario: An installation callback with no session is not associated with anyone
    Given the requester has no DevPulse session
    When an installation callback arrives
    Then the installation is not associated with any user
    And the requester is sent to sign-in

  @ER-INST-002
  Scenario: An installation callback has no installation ID
    Given the user started installation
    When the installation callback arrives without an installation ID
    Then the callback is rejected
    And no installation record is created

  @ER-INST-003 @SR-STATE-002 @security @blocked-by-OQ-017
  Scenario: An installation callback cannot be correlated to the user's request
    Given the user did not start an installation
    When an installation callback arrives for the user
    Then the callback is rejected
    And no installation record is created

  @FR-INST-007 @DR-CONN-002
  Scenario: A duplicate installation callback creates no duplicate
    Given the user completed an installation callback for installation ID 5001
    When the same callback is received again
    Then exactly one installation record exists for installation ID 5001
    And the connection is unchanged

  @FR-INST-007 @DR-CONN-002
  Scenario: Two identical callbacks arrive at the same time
    When two identical installation callbacks for installation ID 5001 arrive concurrently
    Then exactly one installation record exists for installation ID 5001

  @ER-INST-004 @BR-005 @security
  Scenario: The installation is already owned by another user
    Given another DevPulse user already owns installation ID 5001
    When the signed-in user's callback reports installation ID 5001
    Then the callback is rejected
    And installation ID 5001 is still owned by the other user
    And the signed-in user sees a safe message

  @REV2 @FR-INST-010 @DR-CONN-002 @DR-CONN-005
  Scenario: A reconnect returns the user's own disconnected installation ID
    Given the user disconnected installation ID 5001
    And the user chose "Reconnect"
    When the installation callback reports installation ID 5001 and verification confirms it
    Then the existing record for installation ID 5001 becomes the user's current connection
    And that record is updated
    And exactly one record exists for installation ID 5001
    And the user has at most one current connection
    And no separate record is kept for the earlier period

  @REV2 @DR-CONN-001 @blocked-by-OQ-027
  Scenario: The removal-pending marker after a reconnect reactivates the user's own record
    Given the user disconnected installation ID 5001 and the connection was marked removal pending
    When the user reconnects and the existing record is reactivated
    Then the outcome for the removal-pending marker follows the approved decision

  @REV2 @ER-INST-004 @BR-005 @DR-CONN-002 @security
  Scenario: A callback reports an installation ID that belongs to another user's disconnected record
    Given another DevPulse user disconnected installation ID 5001
    When the signed-in user's callback reports installation ID 5001
    Then the callback is rejected
    And the other user's record is left untouched
    And installation ID 5001 is not reassigned to the signed-in user
    And the signed-in user sees a safe message

  @ER-INST-005
  Scenario: Verification does not confirm the installation
    Given the user started installation
    When GitHub returns the user to DevPulse but verification does not confirm the installation
    Then the installation is not marked active
    And the connection state is Verification failed

  @ER-INST-007
  Scenario: GitHub is temporarily unavailable during verification
    Given the user started installation
    When GitHub is temporarily unavailable while DevPulse verifies the installation
    Then the installation is not marked active
    And the user sees a retryable message

  @ER-SYS-002
  Scenario: GitHub rate-limits verification
    Given GitHub is rate-limiting DevPulse
    When DevPulse verifies an installation
    Then the user sees a safe retry-later message
    And the stored connection state is unchanged

  @REV1 @SR-PERM-001
  Scenario: The App requests only the approved minimum permissions
    When the user reviews the permissions requested by the DevPulse GitHub App
    Then no repository-content permission is requested
    And no repository-activity permission is requested
    And no write permission is requested
    And read access to the user's email address is requested

  @REV2 @FR-INST-008
  Scenario Outline: The user opens GitHub's page to manage the installation
    Given the connection state is <state>
    When the user chooses "Manage installation"
    Then the user is taken to GitHub's page for managing the installation

    Examples:
      | state                         |
      | Connected                     |
      | Permission attention required |
      | Suspended                     |
      | Verification failed           |

  @REV2 @DR-CONN-006 @blocked-by-OQ-020
  Scenario: A recorded account type other than "User" is shown as recorded
    Given a connection whose recorded account type is a value other than "User"
    When the user opens Tool Configuration
    Then the account type is shown as recorded
    And no error occurs
```
