# <Feature name>

**Status:** Draft <!-- Draft | Reviewed | Building | Done -->
**Date:** <YYYY-MM-DD>

## 1. Intent

<!-- The developer's request, in their own words. Copy it, do not rewrite it. -->

> ...

## 2. Goal

<!-- One or two sentences: what is better for the user when this works? -->

## 3. Scope

**MVP (the smallest version that works end to end):**

- ...

**Later (wanted, but not in the MVP):**

- ...

**Non-goals (must not be built, stubbed, or shown in the UI):**

- ...

## 4. How it works

<!-- Plain technical notes. Say what, not how to code it. Delete lines that do not apply. -->

- **Data flow:** <!-- for GitHub data: GitHub -> background job -> service -> repository -> PostgreSQL -> API -> UI -->
- **Data kept:** <!-- the information stored, in words (not table definitions) -->
- **API:** <!-- the endpoints or actions the UI needs, in words -->
- **Background jobs:** <!-- what runs, how often, what happens on failure -->
- **UI:** <!-- pages, main components, loading / empty / error states -->
- **Security and privacy:** <!-- ownership, credentials, permissions, anything sensitive -->

## 5. Scenarios

<!-- 5 to 12 scenarios. Happy path first, then the failures and ownership/security cases that matter. -->

```gherkin
Feature: <Feature name>

  Scenario: <happy path>
    Given ...
    When ...
    Then ...

  Scenario: <failure case>
    Given ...
    When ...
    Then ...
```

## 6. Acceptance criteria

<!-- A checklist the developer can tick while reviewing. Each item is observable. -->

- [ ] ...
- [ ] ...
- [ ] No secret appears in logs, responses, or the browser.
- [ ] Tests for the important behavior pass.

## 7. Open questions

<!-- Anything unclear. Give 2 to 4 options and the trade-off. The developer decides; do not decide for them. -->

1. **<Question>**
   - A. ...
   - B. ...
   - Trade-off: ...

## 8. Assumptions

<!-- Things taken as true to get started. The developer can correct them. -->

- ...
