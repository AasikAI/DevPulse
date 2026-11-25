# GitHub connection and scheduled data sync

**Status:** Ready for review (all questions answered)
**Date:** 2026-11-25

## 1. Intent

> Hey i need github authentication and github connection for devpulse, so that devpulse will use some celery or some backgroud jobs will run in schedule to fetch the data from github api endpoints and publish to app db, then from db the widgets , infographics component, dashboard will pull the data

## 2. Goal

A person signs in with GitHub, connects their GitHub account to DevPulse, chooses which repositories to include, and sees a dashboard widget filled from pull request data that background jobs fetched from GitHub on a schedule and stored in the DevPulse database.

## 3. Scope

**MVP (the smallest version that works end to end):**

- Sign in with GitHub. Anyone with a GitHub account can sign in. DevPulse keeps its own user and its own session.
- Connect GitHub by installing the DevPulse GitHub App, and show the connection status.
- Right after connecting, fetch the list of repositories the App can access.
- A repository selection page where the user picks which repositories DevPulse should track.
- A background job that fetches pull request data (open, merged, review state) for the selected repositories only, right after the selection is saved and then every 15 minutes, and saves it to PostgreSQL. The first fetch for a repository covers its whole history.
- One dashboard page with a pull request widget that reads only from the database and shows when the data was last updated.
- Loading, empty, and error states on every new page.
- Everything runs locally with Docker Compose: API, frontend, PostgreSQL, Redis, Celery worker, Celery Beat.

**Later (wanted, not in the MVP):**

- Disconnect and reconnect GitHub
- Profile page and profile refresh
- More GitHub data types, widgets, and infographics (for example CI workflow runs)
- Organisation installations
- Webhooks for faster updates
- A "refresh now" button
- Listing and ending sessions on other devices

**Non-goals (must not be built, stubbed, or shown in the UI):**

- Email-and-password login
- GitLab, Bitbucket, or other providers
- Storing repository source code
- Ranking, scoring, or comparing developers, or labelling counts as productivity or skill

## 4. How it works

- **Data flow:** GitHub -> Celery task (started by Celery Beat, or right after connecting or saving the selection) -> service -> repository -> PostgreSQL -> FastAPI -> React widgets. No page load fetches from GitHub.
- **Data kept:** users (GitHub user ID, username, name, avatar, email if GitHub provides one); sessions (a hash of the session credential only); connections (installation ID, GitHub account, granted permissions, status, last checked time); the repositories the App can access and which of them the user selected (unselecting keeps the stored data but hides it and stops fetching); pull request data for the selected repositories (state, review state, key dates) with its last-fetched time; job runs (status, time, safe failure reason).
- **API:** start sign-in and handle the GitHub callback; current user; logout; start installation and handle its callback; connection status; list repositories and save the selection; read endpoint for the pull request widget data, including the last-updated time.
- **Background jobs:** a Celery worker and Celery Beat introduced by this feature. One task per connection, passed the internal connection ID only, never credentials. Safe to run twice (no duplicate rows). Temporary failures (GitHub down, rate limit) retry with a growing delay; revoked access or missing permissions stop retrying and mark the connection as needing attention. Because the first fetch covers all history, a large repository can take several runs: the job keeps the progress it has made, respects GitHub's rate limits, and continues in the next run.
- **UI:** sign-in page; a connect-GitHub page showing status; a repository selection page; a dashboard page with the pull request widget, a "last updated" time, and prompts when there is no connection or no repository selected.
- **After sign-in:** a user with no connection lands on the connect-GitHub page; a user with a connection lands on the dashboard.
- **Security and privacy:** sign-in uses GitHub only; the user ID from GitHub identifies the user; OAuth state is single-use; the session cookie is HTTP-only; every query is limited to the signed-in user; the GitHub App private key lives outside the database; installation tokens are short-lived and not stored; GitHub user tokens are not stored; no secret in logs, responses, URLs, or browser storage; the App asks for read-only permissions, only what repositories and pull requests need.

## 5. Scenarios

```gherkin
Feature: GitHub connection and scheduled data sync

  Scenario: A new user signs in with GitHub
    Given I have never signed in to DevPulse
    When I choose "Continue with GitHub" and authorize on GitHub
    Then a DevPulse user exists for my GitHub account
    And I am signed in
    And I land on the connect-GitHub page

  Scenario: A returning user with a connection signs in again
    Given I have signed in before and have a connection
    When I sign in with GitHub again
    Then I am signed in as the same DevPulse user
    And no second user is created
    And I land on the dashboard

  Scenario: Sign-in is cancelled or fails
    When I cancel on GitHub, or the sign-in response is invalid or reused
    Then I am not signed in
    And I see a safe message and can try again

  Scenario: I connect my GitHub account
    Given I am signed in and have no connection
    When I install the DevPulse GitHub App
    Then DevPulse shows my connection as connected
    And the connection belongs to me only
    And DevPulse fetches the list of repositories the App can access

  Scenario: I choose which repositories to track
    Given I am connected and DevPulse shows my repositories
    When I select some repositories and save
    Then DevPulse fetches pull request data for those repositories right away
    And only the selected repositories are fetched from then on

  Scenario: I stop tracking a repository
    Given I am tracking a repository and its pull request data is stored
    When I unselect the repository
    Then DevPulse stops fetching it and hides its data
    And the stored data is kept
    And selecting it again shows the data and resumes fetching

  Scenario: The dashboard guides me when there is nothing to show
    Given I am signed in and <situation>
    When I open the dashboard
    Then I see <prompt> and no widget data

    Examples:
      | situation                                   | prompt                                  |
      | I have no connection                        | a prompt to connect GitHub              |
      | I am connected and have selected nothing    | a prompt to select repositories         |

  Scenario: The scheduled job stores pull request data
    Given I am connected and have selected repositories
    When the scheduled job runs, every 15 minutes
    Then pull request data for my selected repositories is saved in the database
    And running the job again does not create duplicates

  Scenario: The widget reads from the database
    Given the database holds my pull request data
    When I open the dashboard
    Then the widget shows that data and when it was last updated
    And no request is sent to GitHub while the page loads

  Scenario: GitHub is temporarily unavailable
    Given I have stored data from an earlier run
    When a scheduled run fails because GitHub is down or rate-limiting
    Then the dashboard still shows the earlier data marked as out of date
    And the run is retried later

  Scenario: Access is removed on GitHub
    Given my connection exists
    When a scheduled run finds the App was removed or lost a permission
    Then the job stops retrying
    And the connection shows that it needs attention

  Scenario: I only see my own data
    Given another user also has a connection and stored data
    When I open the dashboard
    Then I see only my own data

  Scenario: I log out
    Given I am signed in on two browsers
    When I log out on one
    Then that session ends and the other stays signed in
    And my connection and stored data are unchanged
```

## 6. Acceptance criteria

- [ ] I can sign in with GitHub and am still signed in after a browser refresh.
- [ ] After sign-in I land on the connect-GitHub page without a connection, and on the dashboard with one.
- [ ] I can connect my GitHub account and see its status.
- [ ] After connecting, I see the repositories the App can access and can pick which to track.
- [ ] Pull request data for the selected repositories is fetched right after I save the selection, then every 15 minutes, without duplicates.
- [ ] The first fetch covers each repository's whole history; a large history finishes over several runs without breaking GitHub's rate limits, and keeps its progress.
- [ ] Unselecting a repository hides its data and stops fetching it; the data is kept and returns when I select it again.
- [ ] The dashboard widget shows data read from the database, with a "last updated" time.
- [ ] Opening the dashboard never calls GitHub.
- [ ] When GitHub fails, earlier data stays visible and is marked out of date; errors shown are safe.
- [ ] Another user's data is never visible to me.
- [ ] No secret appears in logs, responses, URLs, or browser storage.
- [ ] `docker compose up` starts the API, frontend, PostgreSQL, Redis, Celery worker, and Celery Beat.
- [ ] Tests for the important behavior pass.

## 7. Open questions

None right now. Everything asked so far is answered below.

**Decided by you (2026-11-25):**

- MVP data: repositories and pull requests (open, merged, review state); the widget shows pull request counts over time.
- Schedule: every 15 minutes. After connecting, DevPulse fetches the repository list; after the selection is saved, it fetches pull request data right away, then every 15 minutes.
- History: the first fetch covers all history.
- Repositories: the user picks them inside DevPulse after connecting. Unselecting a repository keeps its stored data, hides it, and stops fetching it.
- After sign-in: connect-GitHub page without a connection, dashboard with one.
- Sign-in: anyone with a GitHub account; each user sees only their own data.

## 8. Assumptions

Carried over from earlier decisions in this project. Tell me if the lighter approach should change any of them:

- Sign-in is through a GitHub App, with one GitHub App for both sign-in and installation.
- DevPulse authentication and the GitHub connection are separate: signing in does not connect GitHub.
- Personal GitHub accounts only; one connection per user.
- Sessions are opaque and stored in PostgreSQL as a hash; GitHub user tokens are not stored.
- Times are stored in UTC and shown labelled as UTC.

New in this version:

- The repository list is refreshed on each scheduled run so new repositories appear in the selection page.
- A user can only select repositories the App can access (what they allowed on GitHub's installation screen).
- A signed-in user who is connected but has selected nothing sees a prompt to select repositories on the dashboard.

Decided in the plan, and reviewed by you before coding: session lifetime, cookie and CSRF details, the exact read-only GitHub permission list, how the all-history fetch is split across runs, retry timings, the widget's time grouping, and the Docker Compose layout.
