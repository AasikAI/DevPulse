import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "../../App";
import { AuthProvider } from "../auth/hooks/AuthProvider";
import { aliceUser, connectedAs, notConnected, stubApi } from "../../test/stubApi";

// ECharts needs a real canvas, which the test environment does not have. The chart is a thin
// wrapper around the library, so it is replaced by a stand-in that shows what it was given.
vi.mock("./components/WeeklyChart", () => ({
  default: ({ weekly }: { weekly: unknown[] }) => <div data-testid="weekly-chart">{weekly.length} weeks drawn</div>,
}));

const SUMMARY = "GET /api/pull-requests/summary?weeks=12";
const CONNECTION = "GET /api/github/connection";
const auth = { "GET /api/auth/me": { status: 200, body: aliceUser } };
const shell = { ...auth, [CONNECTION]: { status: 200, body: connectedAs() } };

function weeklyOf(weeks: number, counts: Record<number, [number, number]> = {}) {
  const first = Date.UTC(2026, 8, 7) - (12 - weeks) * 7 * 86_400_000;
  return Array.from({ length: weeks }, (_, i) => ({
    week_start: new Date(first + i * 7 * 86_400_000).toISOString().slice(0, 10),
    opened: counts[i]?.[0] ?? 0,
    merged: counts[i]?.[1] ?? 0,
  }));
}

function summaryOf(overrides: Record<string, unknown> = {}) {
  const weeks = (overrides.weeks as number | undefined) ?? 12;
  return {
    connection_status: "active",
    connection_reason: null,
    repository_count: 2,
    weeks,
    window_start: "2026-09-07",
    last_updated_at: "2026-11-26T10:30:00Z",
    is_stale: false,
    stale_reason: null,
    history_complete: true,
    history_repositories_total: 2,
    history_repositories_complete: 2,
    totals: { open_now: 4, opened_in_window: 9, merged_in_window: 6 },
    open_by_review_state: { none: 1, commented: 0, approved: 2, changes_requested: 1, not_loaded: 0 },
    weekly: weeklyOf(weeks, { 10: [4, 2], 11: [5, 4] }),
    ...overrides,
  };
}

const ok = (body: unknown) => ({ status: 200, body });

function renderApp(path = "/dashboard") {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <AuthProvider>
        <App />
      </AuthProvider>
    </MemoryRouter>,
  );
}

afterEach(() => {
  vi.useRealTimers();
});

// --- Loading, error and prompts -----------------------------------------------------------------


describe("dashboard: states", () => {
  it("shows a loading state while the numbers are being loaded", async () => {
    stubApi({ ...shell, [SUMMARY]: "pending" });
    renderApp();

    expect(await screen.findByText("Loading your pull requests…")).toBeInTheDocument();
  });

  it("shows an error with a retry when the numbers cannot be loaded", async () => {
    let attempts = 0;
    stubApi({ ...shell, [SUMMARY]: () => (++attempts === 1 ? { status: 500 } : ok(summaryOf())) });
    renderApp();

    expect(await screen.findByRole("alert")).toHaveTextContent("Could not load the dashboard");
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));

    expect(await screen.findByRole("heading", { name: "Pull requests per week" })).toBeInTheDocument();
  });

  it("prompts to connect GitHub when there is no connection, and shows no data", async () => {
    stubApi({
      ...auth,
      [CONNECTION]: ok(notConnected),
      [SUMMARY]: ok(summaryOf({ connection_status: "not_connected", repository_count: 0, weekly: [], totals: { open_now: 0, opened_in_window: 0, merged_in_window: 0 } })),
    });
    renderApp();

    expect(await screen.findByRole("heading", { name: /connect github to see your pull requests/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /connect github/i })).toHaveAttribute("href", "/connect");
    expect(screen.queryByTestId("weekly-chart")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Time window")).not.toBeInTheDocument();
  });

  it("prompts to select repositories when connected with nothing selected, and shows no data", async () => {
    stubApi({
      ...shell,
      [SUMMARY]: ok(summaryOf({ repository_count: 0, history_repositories_total: 0, history_repositories_complete: 0 })),
    });
    renderApp();

    expect(await screen.findByRole("heading", { name: /choose the repositories to track/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /select repositories/i })).toHaveAttribute("href", "/repositories");
    expect(screen.queryByTestId("weekly-chart")).not.toBeInTheDocument();
    expect(screen.queryByText("Open now")).not.toBeInTheDocument();
  });
});

// --- The widget ------------------------------------------------------------------------------------


describe("dashboard: pull request widget", () => {
  it("shows the numbers read from DevPulse, the scope, and when they were last updated in UTC", async () => {
    stubApi({ ...shell, [SUMMARY]: ok(summaryOf()) });
    renderApp();

    expect(await screen.findByRole("heading", { name: "Pull requests per week" })).toBeInTheDocument();
    const cards = within(screen.getByText("Open now").closest(".kpi-grid") as HTMLElement);
    expect(cards.getByText("Open now").parentElement).toHaveTextContent("4");
    expect(cards.getByText("Opened").parentElement).toHaveTextContent("9");
    expect(cards.getByText("Merged").parentElement).toHaveTextContent("6");
    expect(screen.getByText(/2 selected repositories · last 12 weeks · weeks start Monday, UTC/)).toBeInTheDocument();
    expect(screen.getByText(/Last updated 26 Nov 2026, 10:30 UTC/)).toBeInTheDocument();
    expect(screen.getByTestId("weekly-chart")).toHaveTextContent("12 weeks drawn");
  });

  it("gives the chart a text description and the same numbers as a table", async () => {
    stubApi({ ...shell, [SUMMARY]: ok(summaryOf()) });
    renderApp();
    await screen.findByTestId("weekly-chart");

    expect(screen.getByRole("img", { name: /9 opened and 6 merged in total/ })).toBeInTheDocument();
    await userEvent.click(screen.getByText("View as a table"));
    const table = screen.getByRole("table");
    const rows = within(table).getAllByRole("row");
    expect(rows).toHaveLength(13); // header + 12 weeks
    expect(rows[12]).toHaveTextContent("this week, in progress");
    expect(rows[12]).toHaveTextContent("5");
    expect(rows[11]).toHaveTextContent("4");
  });

  it("lists open pull requests by review state", async () => {
    stubApi({ ...shell, [SUMMARY]: ok(summaryOf()) });
    renderApp();

    const card = (await screen.findByRole("heading", { name: "Open pull requests by review state" })).closest("section") as HTMLElement;

    expect(within(card).getByText("Approved").nextSibling).toHaveTextContent("2");
    expect(within(card).getByText("Changes requested").nextSibling).toHaveTextContent("1");
    expect(within(card).getByText("Review state not loaded yet").nextSibling).toHaveTextContent("0");
  });

  it("offers 4, 12, 26 and 52 weeks and reloads the numbers when the window changes", async () => {
    const { calls } = stubApi({
      ...shell,
      [SUMMARY]: ok(summaryOf()),
      "GET /api/pull-requests/summary?weeks=26": ok(summaryOf({ weeks: 26 })),
    });
    renderApp();
    const select = await screen.findByLabelText("Time window");

    expect(within(select).getAllByRole("option").map((o) => o.textContent)).toEqual([
      "Last 4 weeks",
      "Last 12 weeks",
      "Last 26 weeks",
      "Last 52 weeks",
    ]);
    await userEvent.selectOptions(select, "26");

    expect(await screen.findByText(/last 26 weeks · weeks start Monday/)).toBeInTheDocument();
    expect(screen.getByTestId("weekly-chart")).toHaveTextContent("26 weeks drawn");
    expect(calls).toContain("GET /api/pull-requests/summary?weeks=26");
  });

  it("says so when there were no pull requests in the period", async () => {
    stubApi({
      ...shell,
      [SUMMARY]: ok(summaryOf({ totals: { open_now: 0, opened_in_window: 0, merged_in_window: 0 }, weekly: weeklyOf(12), open_by_review_state: { none: 0, commented: 0, approved: 0, changes_requested: 0, not_loaded: 0 } })),
    });
    renderApp();

    expect(await screen.findByText("No pull requests were opened or merged in the last 12 weeks.")).toBeInTheDocument();
    expect(screen.queryByTestId("weekly-chart")).not.toBeInTheDocument();
  });

  it("never uses productivity, ranking or people language", async () => {
    stubApi({ ...shell, [SUMMARY]: ok(summaryOf()) });
    renderApp();
    await screen.findByTestId("weekly-chart");

    expect(document.body.textContent).not.toMatch(/productiv|perform|rank|score|leaderboard|top contributor|developer|author/i);
  });

  it("only talks to DevPulse, never to GitHub", async () => {
    const { calls } = stubApi({ ...shell, [SUMMARY]: ok(summaryOf()) });
    renderApp();
    await screen.findByTestId("weekly-chart");

    expect(calls.every((call) => call.split(" ")[1].startsWith("/api/"))).toBe(true);
    expect(calls.join(" ")).not.toMatch(/github\.com/);
  });

  it("keeps credentials out of the page and out of browser storage", async () => {
    stubApi({ ...shell, [SUMMARY]: ok(summaryOf()) });
    renderApp();
    await screen.findByTestId("weekly-chart");

    expect(localStorage).toHaveLength(0);
    expect(sessionStorage).toHaveLength(0);
    expect(document.body.textContent).not.toMatch(/ghu_|ghs_|ghp_|bearer|installation_id|devpulse_session/i);
  });
});

// --- Importing and freshness -----------------------------------------------------------------------


describe("dashboard: importing history", () => {
  const importing = (done = 1) =>
    summaryOf({
      history_complete: false,
      history_repositories_total: 3,
      history_repositories_complete: done,
      repository_count: 3,
      totals: { open_now: 0, opened_in_window: 0, merged_in_window: 0 },
      weekly: weeklyOf(12),
    });

  it("says how far the import has got and waits for the first numbers", async () => {
    stubApi({ ...shell, [SUMMARY]: ok(importing()) });
    renderApp();

    expect(await screen.findByText(/Importing history: 1 of 3 repositories/)).toBeInTheDocument();
    expect(screen.getByText("Waiting for the first import to bring in pull requests.")).toBeInTheDocument();
  });

  it("keeps checking while the import runs and shows the numbers when they arrive", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    let calls = 0;
    stubApi({ ...shell, [SUMMARY]: () => (++calls < 2 ? ok(importing()) : ok(summaryOf())) });
    renderApp();
    await screen.findByText(/Numbers will grow as it finishes/);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(30_500);
    });

    expect(await screen.findByTestId("weekly-chart")).toBeInTheDocument();
    expect(screen.queryByText(/Numbers will grow as it finishes/)).not.toBeInTheDocument();
  });

  it("stops checking after five minutes and offers to reload", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    stubApi({ ...shell, [SUMMARY]: ok(importing()) });
    renderApp();
    await screen.findByText(/Numbers will grow as it finishes/);

    for (let tick = 0; tick < 11; tick++) {
      await act(async () => {
        await vi.advanceTimersByTimeAsync(30_500);
      });
    }

    expect(await screen.findByText(/Still importing/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reload" })).toBeInTheDocument();
  });

  it("does not keep checking once the data is complete", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const { calls } = stubApi({ ...shell, [SUMMARY]: ok(summaryOf()) });
    renderApp();
    await screen.findByTestId("weekly-chart");

    await act(async () => {
      await vi.advanceTimersByTimeAsync(120_000);
    });

    expect(calls.filter((c) => c === SUMMARY)).toHaveLength(1);
  });
});

describe("dashboard: out of date and needs attention", () => {
  it("keeps showing the earlier data and marks it out of date when the latest update failed", async () => {
    stubApi({ ...shell, [SUMMARY]: ok(summaryOf({ is_stale: true, stale_reason: "last_run_failed" })) });
    renderApp();

    const banner = await screen.findByText("Out of date.");

    expect(banner.parentElement).toHaveTextContent(/latest update could not finish/);
    expect(banner.parentElement).toHaveTextContent("Showing data from 26 Nov 2026, 10:30 UTC");
    expect(screen.getByTestId("weekly-chart")).toBeInTheDocument(); // the stored data is still there
    expect(screen.getByText("Open now").parentElement).toHaveTextContent("4");
  });

  it("marks data out of date when it has not been refreshed for a while", async () => {
    stubApi({ ...shell, [SUMMARY]: ok(summaryOf({ is_stale: true, stale_reason: "not_updated_recently" })) });
    renderApp();

    expect((await screen.findByText("Out of date.")).parentElement).toHaveTextContent(/not been refreshed recently/);
  });

  it("does not mark fresh data as out of date", async () => {
    stubApi({ ...shell, [SUMMARY]: ok(summaryOf()) });
    renderApp();
    await screen.findByTestId("weekly-chart");

    expect(screen.queryByText("Out of date.")).not.toBeInTheDocument();
  });

  it.each([
    ["access_revoked", /can no longer access your GitHub account/],
    ["permission_missing", /missing a read permission/],
    ["suspended", /suspended/],
  ])("explains %s, links to the fix, and still shows the stored data", async (reason, message) => {
    stubApi({
      ...shell,
      [SUMMARY]: ok(summaryOf({ connection_status: "needs_attention", connection_reason: reason, is_stale: true, stale_reason: "not_updated_recently" })),
    });
    renderApp();

    const alert = await screen.findByRole("alert");

    expect(alert).toHaveTextContent("GitHub needs your attention.");
    expect(alert).toHaveTextContent(message);
    expect(within(alert).getByRole("link", { name: /review access on github/i })).toHaveAttribute("href", "/connect");
    expect(screen.getByTestId("weekly-chart")).toBeInTheDocument();
    expect(screen.queryByText("Out of date.")).not.toBeInTheDocument(); // one clear warning, not two
  });
});

// --- Landing, navigation and the setup pages -------------------------------------------------------------


describe("after sign-in", () => {
  it("sends a user with a connection to the dashboard", async () => {
    stubApi({ ...shell, [SUMMARY]: ok(summaryOf()) });
    renderApp("/start");

    expect(await screen.findByRole("heading", { name: "Pull requests" })).toBeInTheDocument();
  });

  it("sends a user whose connection needs attention to the dashboard too", async () => {
    stubApi({
      ...auth,
      [CONNECTION]: ok(connectedAs({ status: "needs_attention", reason: "suspended" })),
      [SUMMARY]: ok(summaryOf({ connection_status: "needs_attention", connection_reason: "suspended" })),
    });
    renderApp("/start");

    expect(await screen.findByRole("heading", { name: "Pull requests" })).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent("GitHub needs your attention.");
  });

  it("sends a user without a connection to the connect page", async () => {
    stubApi({ ...auth, [CONNECTION]: ok(notConnected) });
    renderApp("/start");

    expect(await screen.findByRole("heading", { name: "Your next insight starts here." })).toBeInTheDocument();
  });

  it("shows an error with a retry when the connection cannot be checked", async () => {
    let attempts = 0;
    stubApi({ ...auth, [CONNECTION]: () => (++attempts === 1 ? { status: 500 } : ok(notConnected)) });
    renderApp("/start");

    expect(await screen.findByRole("alert")).toHaveTextContent("Could not load your GitHub connection");
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));

    expect(await screen.findByRole("heading", { name: "Your next insight starts here." })).toBeInTheDocument();
  });
});

describe("navigation", () => {
  it("has a sidebar with Overview, Repositories and GitHub connection, marking the current page", async () => {
    stubApi({ ...shell, [SUMMARY]: ok(summaryOf()) });
    renderApp();
    const nav = await screen.findByRole("navigation", { name: "Primary" });

    expect(within(nav).getByRole("link", { name: "Overview" })).toHaveAttribute("href", "/dashboard");
    expect(within(nav).getByRole("link", { name: "Overview" })).toHaveAttribute("aria-current", "page");
    expect(within(nav).getByRole("link", { name: "Repositories" })).toHaveAttribute("href", "/repositories");
    expect(within(nav).getByRole("link", { name: "GitHub connection" })).toHaveAttribute("href", "/connect");
  });

  it("shows the connection status in the sidebar", async () => {
    stubApi({ ...shell, [SUMMARY]: ok(summaryOf()) });
    renderApp();

    expect(await screen.findByText("GitHub connected")).toBeInTheDocument();
    expect(screen.getByText("3 repositories available")).toBeInTheDocument();
  });

  it("lets me log out from the dashboard", async () => {
    stubApi({ ...shell, [SUMMARY]: ok(summaryOf()), "POST /api/auth/logout": { status: 204 } });
    renderApp();

    await userEvent.click(await screen.findByRole("button", { name: "Log out" }));

    expect(await screen.findByRole("heading", { name: "Sign in to DevPulse" })).toBeInTheDocument();
  });

  it("gives the connect page a way back to the dashboard once connected", async () => {
    stubApi({ ...shell, [SUMMARY]: ok(summaryOf()) });
    renderApp("/connect");

    expect(await screen.findByRole("link", { name: "Back to dashboard" })).toHaveAttribute("href", "/dashboard");
  });

  it("does not offer a way back to the dashboard before connecting", async () => {
    stubApi({ ...auth, [CONNECTION]: ok(notConnected) });
    renderApp("/connect");
    await screen.findByRole("heading", { name: "Your next insight starts here." });

    expect(screen.queryByRole("link", { name: "Back to dashboard" })).not.toBeInTheDocument();
  });

  it("gives the repository selection page a way back to the dashboard", async () => {
    stubApi({
      ...auth,
      "GET /api/repositories?page=1&page_size=50": ok({
        list_status: "ready",
        refreshed_at: "2026-11-26T10:30:00Z",
        total: 1,
        selected_count: 0,
        page: 1,
        page_size: 50,
        items: [{ id: "r1", full_name: "alice-dev/repo-1", is_private: false, is_selected: false }],
      }),
    });
    renderApp("/repositories");

    const links = await screen.findAllByRole("link", { name: "Back to dashboard" });

    expect(links.length).toBeGreaterThan(0);
    links.forEach((link) => expect(link).toHaveAttribute("href", "/dashboard"));
  });
});
