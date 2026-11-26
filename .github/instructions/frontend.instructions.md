---
applyTo: "frontend/**/*.{ts,tsx}"
---

# DevPulse React and TypeScript Instructions

## General

- Use TypeScript for frontend code.
- Use functional React components.
- Use explicit types for component props, API contracts, and state.
- Avoid `any`; if unavoidable, document the boundary and narrow it immediately.
- Prefer small feature-focused components over large page components.
- Do not add a state-management library without asking first.

## Feature organization

Organize frontend code by feature where practical:

```text
src/features/<feature>/
├── api/
├── components/
├── hooks/
├── pages/
├── types/
└── utils/
```

Place truly shared UI components in a shared component area. Do not move feature-specific behavior into shared components prematurely.

## API access

- React must call DevPulse FastAPI endpoints, not GitHub directly.
- Keep API calls in feature-specific API or service modules.
- Use typed request and response contracts.
- Handle authentication failures consistently.
- Do not store GitHub tokens or session credentials in JavaScript-accessible storage.
- Do not place sensitive values in URLs.

## Authentication UI

- Restore the current DevPulse session through a server-backed current-user endpoint.
- Protect authenticated routes.
- Distinguish application authentication from GitHub installation status.
- Logging out must clear local user state but must not assume the GitHub installation was removed.
- Disconnecting GitHub must not log the user out.
- Validate post-login redirect targets. Allow only known in-application routes; never redirect to an arbitrary or external URL (no open redirects).

## User experience states

Every data-driven page must have at least loading, empty, and error states, even in an MVP slice. Add the other states below when the feature has them; visual polish can wait for the UI/UX pass.

States to consider:

- Loading
- Success
- Empty
- Stale data
- Partial data
- Synchronizing
- Rate limited
- Permission required
- Recoverable error
- Unrecoverable error
- Backend unavailable

When synchronization fails, continue showing the latest stored data when available and clearly show its freshness.

## Accessibility

- Use semantic HTML.
- Associate labels with inputs.
- Ensure keyboard access to all controls.
- Keep visible focus indicators.
- Do not communicate status through color alone.
- Provide accessible names for icon buttons.
- Provide textual summaries, labels, or equivalent alternatives for charts.
- Target WCAG 2.2 AA contrast.

## Charts and analytics

- Use Apache ECharts for charts and visualizations.
- Read chart data from PostgreSQL-backed FastAPI endpoints.
- Do not calculate authoritative business metrics independently in React.
- Display the selected date and repository scope.
- Display the last successful synchronization or data-freshness indicator where relevant.
- Do not label commit count, pull-request count, or technology detection as productivity or skill.

## Error handling

- Show safe, actionable messages.
- Do not display stack traces, raw GitHub errors, tokens, or internal database details.
- Provide retry actions only when retry is valid.
- Preserve valid user input after recoverable failures.

## Frontend testing

Write tests in the same slice as the UI code. Strict test-first is not required.

- Use Vitest and React Testing Library.
- Test user-observable behavior rather than implementation details.
- Cover the user-visible behavior of each slice, including loading, empty, and error states. Add stale, partial, rate-limited, and permission states when the feature has them.
- Use the scenarios in the feature's `spec.md` as the source for test names and cases.
- Mock FastAPI at the network boundary.
- Use Playwright for a few key journeys.
- Never include real credentials in test data.
