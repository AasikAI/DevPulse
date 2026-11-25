# GitHub profile: behaviour specification

```gherkin
Feature: GitHub profile
  The Profile is a section of its own that shows the user's authorized GitHub profile data.
  Refreshing the profile sends the user through GitHub authorization again.

  Background:
    Given the user is signed in as GitHub account ID 1001

  @FR-PROF-002 @UI-PROF-001
  Scenario: The Profile shows the user's metadata
    When the user opens the Profile section
    Then the Profile shows the name, avatar, username, email, GitHub profile link and account type
    And the Profile shows the account creation time, last login time and last profile refresh time
    And the Profile is separate from Tool Configuration

  @FR-PROF-001 @DR-USER-002 @DR-USER-003
  Scenario: Profile metadata is stored when the user authenticates
    When the user signs in with GitHub
    Then the authorized GitHub profile metadata is stored for the user
    And every stored time is a UTC time with a time zone

  @FR-PROF-003 @BR-008
  Scenario: The Profile handles a missing email
    Given GitHub provides no email for the user
    When the user opens the Profile section
    Then the Profile shows "Email not available from GitHub"
    And no invented email is shown

  @REV1 @FR-PROF-006
  Scenario: The Profile handles a missing display name
    Given GitHub provides no display name for the user
    When the user opens the Profile section
    Then the Profile shows "Name not provided by GitHub" as the name
    And the username is not shown in place of the name

  @REV1 @FR-PROF-004
  Scenario: The user chooses to refresh the profile
    When the user chooses "Refresh" on the Profile
    Then the user is taken to GitHub to authorize DevPulse again

  @REV1 @FR-PROF-004 @FR-PROF-005
  Scenario: A refresh updates changed metadata
    Given the user's GitHub display name and avatar have changed on GitHub
    When the user chooses "Refresh", authorizes DevPulse on GitHub and returns to DevPulse
    Then the Profile shows the new display name and avatar
    And the Profile shows a refresh confirmation
    And the last profile refresh time shown is the time of this refresh

  @REV1 @FR-PROF-005 @BR-001 @DR-USER-001
  Scenario: The user's identity stays stable when the username changes
    Given the user's GitHub username has changed on GitHub
    When the user chooses "Refresh", authorizes DevPulse on GitHub and returns to DevPulse
    Then the Profile shows the new username
    And the user is still the same DevPulse user for GitHub account ID 1001
    And no second user exists

  @REV1 @ER-PROF-001
  Scenario: The user cancels at GitHub during a refresh
    Given the user chose "Refresh"
    When the user cancels on the GitHub authorization page
    Then the stored profile is unchanged
    And the user sees a safe message

  @REV1 @ER-PROF-001
  Scenario: GitHub denies authorization during a refresh
    Given the user chose "Refresh"
    When GitHub returns an access-denied result to DevPulse
    Then the stored profile is unchanged
    And the user sees a safe message

  @REV1 @ER-PROF-002
  Scenario: The refresh fails temporarily
    Given the user chose "Refresh"
    And GitHub is temporarily unavailable
    When the user returns to DevPulse
    Then the stored profile is kept
    And the Profile shows when it was last refreshed
    And the user can try again

  @ER-SYS-002
  Scenario: GitHub rate-limits a refresh
    Given GitHub is rate-limiting DevPulse
    When the user chooses "Refresh", authorizes DevPulse on GitHub and returns to DevPulse
    Then the user sees a safe retry-later message
    And the stored profile is unchanged

  @REV1 @ER-PROF-003 @BR-001 @security
  Scenario: A refresh authorized by a different GitHub account is rejected
    Given the user chose "Refresh"
    When a different GitHub account, with ID 2002, authorizes DevPulse
    Then the refresh is rejected
    And the stored profile of GitHub account ID 1001 is unchanged
    And the user sees a safe message

  @REV2 @ER-AUTH-008 @SR-STATE-001 @ER-AUTH-004 @ER-AUTH-005 @ER-AUTH-006 @ER-AUTH-007 @security @blocked-by-OQ-012
  Scenario Outline: A refresh callback with an invalid state value is rejected
    Given the user chose "Refresh"
    When the refresh callback arrives <problem>
    Then the callback is rejected
    And the stored profile is unchanged

    Examples:
      | problem                                       |
      | without a state value                         |
      | with a state value DevPulse never issued      |
      | with a state value whose lifetime has elapsed |
      | with a state value that was already used      |
      | from a browser that did not start the refresh |

  @REV1 @SR-CSRF-001 @security @blocked-by-OQ-013
  Scenario: A forged cross-site profile refresh is rejected
    When another website submits a profile refresh request using the user's session cookie
    Then the request is rejected
    And the stored profile is unchanged

  @SR-CRED-005 @security
  Scenario: Profile data exposes no credential
    When the user opens the Profile section
    Then no token or session credential appears in what the browser receives or shows

  @SR-AUTHZ-001 @security
  Scenario: One user cannot read another user's profile
    Given another signed-in user exists as GitHub account ID 2002
    When the user requests the profile of GitHub account ID 2002
    Then access is denied
    And none of the other user's profile data is returned

  @UI-PROF-002
  Scenario: A neutral placeholder hints at later phases
    When the Profile mentions repository activity
    Then it shows only "Not yet synchronized"
    And it shows no repository activity or counts

  @SR-PRIV-001
  Scenario: Only the approved profile attributes are stored
    When the user signs in with GitHub
    Then DevPulse stores only the profile attributes listed in the approved data requirements

  @REV1 @UI-STATE-001 @ER-SYS-001
  Scenario Outline: The Profile handles each loading and failure condition
    When <condition>
    Then the Profile shows <outcome>

    Examples:
      | condition                         | outcome                                          |
      | the Profile is loading            | a loading state                                  |
      | the Profile fails to load         | a recoverable error with a retry action          |
      | the DevPulse backend is unavailable | a safe unavailable state                       |

  @REV1 @UI-TIME-001
  Scenario Outline: Times are displayed in UTC and labelled as UTC
    Given the user has a stored time of "2026-11-16 09:26" in UTC
    When the user views <page>
    Then <time> is displayed as "16 Nov 2026, 09:26 UTC"

    Examples:
      | page               | time                         |
      | the Profile        | the last login time          |
      | the Profile        | the account creation time    |
      | the Profile        | the last profile refresh time |
      | Tool Configuration | the last verification time   |
```
