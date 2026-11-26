import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "../../App";
import { AuthProvider } from "../auth/hooks/AuthProvider";
import { aliceUser, stubApi } from "../../test/stubApi";

const LIST = "GET /api/repositories?page=1&page_size=50";
const SAVE = "POST /api/repositories/selection";

type Item = { id: string; full_name: string; is_private: boolean; is_selected: boolean };

const item = (n: number, overrides: Partial<Item> = {}): Item => ({
  id: `repo-id-${n}`,
  full_name: `alice-dev/repo-${n}`,
  is_private: false,
  is_selected: false,
  ...overrides,
});

function listOf(items: Item[], overrides: Record<string, unknown> = {}) {
  return {
    list_status: "ready",
    refreshed_at: "2026-11-26T10:30:00Z",
    total: items.length,
    selected_count: items.filter((i) => i.is_selected).length,
    page: 1,
    page_size: 50,
    items,
    ...overrides,
  };
}

const auth = { "GET /api/auth/me": { status: 200, body: aliceUser } };

function renderPage() {
  return render(
    <MemoryRouter initialEntries={["/repositories"]}>
      <AuthProvider>
        <App />
      </AuthProvider>
    </MemoryRouter>,
  );
}

function savedBody(fetchStub: ReturnType<typeof stubApi>["fetchStub"]) {
  const call = fetchStub.mock.calls.find(([url]) => url === "/api/repositories/selection");
  return call ? JSON.parse(String((call[1] as RequestInit).body)) : undefined;
}

afterEach(() => {
  vi.useRealTimers();
});

describe("select repositories: states", () => {
  it("shows a loading state while the repositories are being loaded", async () => {
    stubApi({ ...auth, [LIST]: "pending" });
    renderPage();

    expect(await screen.findByText("Loading your repositories…")).toBeInTheDocument();
  });

  it("shows an error with a retry when the list cannot be loaded", async () => {
    let attempts = 0;
    stubApi({
      ...auth,
      [LIST]: () => (++attempts === 1 ? { status: 500 } : { status: 200, body: listOf([item(1)]) }),
    });
    renderPage();

    expect(await screen.findByRole("alert")).toHaveTextContent("Could not load your repositories");
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));

    expect(await screen.findByText("alice-dev/repo-1")).toBeInTheDocument();
  });

  it("asks the user to connect GitHub first when there is no connection", async () => {
    stubApi({ ...auth, [LIST]: { status: 409, body: { code: "not_connected", message: "Connect first." } } });
    renderPage();

    expect(await screen.findByText(/connect your github account before choosing/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /connect github/i })).toHaveAttribute("href", "/connect");
  });

  it("says the repositories are being fetched until the background job has run", async () => {
    stubApi({ ...auth, [LIST]: { status: 200, body: listOf([], { list_status: "syncing", refreshed_at: null }) } });
    renderPage();

    expect(await screen.findByText("Fetching your repositories…")).toBeInTheDocument();
    expect(screen.queryByRole("searchbox")).not.toBeInTheDocument();
  });

  it("keeps checking while the repositories are fetched and then shows them", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    let calls = 0;
    stubApi({
      ...auth,
      [LIST]: () =>
        ++calls < 2
          ? { status: 200, body: listOf([], { list_status: "syncing", refreshed_at: null }) }
          : { status: 200, body: listOf([item(1), item(2)]) },
    });
    renderPage();
    await screen.findByText("Fetching your repositories…");

    await act(async () => {
      await vi.advanceTimersByTimeAsync(3100);
    });

    expect(await screen.findByText("alice-dev/repo-2")).toBeInTheDocument();
  });

  it("stops checking after a while and offers to check again", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    stubApi({ ...auth, [LIST]: { status: 200, body: listOf([], { list_status: "syncing", refreshed_at: null }) } });
    renderPage();
    await screen.findByText("Fetching your repositories…");

    for (let tick = 0; tick < 21; tick++) {
      await act(async () => {
        await vi.advanceTimersByTimeAsync(3100);
      });
    }

    expect(await screen.findByText(/taking longer than expected/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Check again" })).toBeInTheDocument();
  });

  it("explains an empty list and offers to check again", async () => {
    stubApi({ ...auth, [LIST]: { status: 200, body: listOf([]) } });
    renderPage();

    expect(await screen.findByText("No repositories available yet.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Check again" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Save selection" })).toBeDisabled();
  });
});

describe("select repositories: choosing", () => {
  it("lists the repositories with the saved choices ticked and private ones labelled", async () => {
    stubApi({
      ...auth,
      [LIST]: {
        status: 200,
        body: listOf([item(1, { is_selected: true }), item(2, { is_private: true }), item(3)]),
      },
    });
    renderPage();

    expect(await screen.findByRole("checkbox", { name: /repo-1/ })).toBeChecked();
    expect(screen.getByRole("checkbox", { name: /repo-2/ })).not.toBeChecked();
    expect(screen.getByText("Private")).toBeInTheDocument();
    expect(screen.getByText("1 selected")).toBeInTheDocument();
    expect(screen.getByText(/3 available/)).toBeInTheDocument();
  });

  it("counts unsaved changes and lets me undo one by ticking it back", async () => {
    stubApi({ ...auth, [LIST]: { status: 200, body: listOf([item(1, { is_selected: true }), item(2)]) } });
    renderPage();
    const save = () => screen.getByRole("button", { name: /save selection/i });
    expect(await screen.findByRole("checkbox", { name: /repo-2/ })).toBeInTheDocument();
    expect(save()).toBeDisabled();

    await userEvent.click(screen.getByRole("checkbox", { name: /repo-2/ }));
    await userEvent.click(screen.getByRole("checkbox", { name: /repo-1/ }));

    expect(screen.getByText("1 selected")).toBeInTheDocument(); // 1 saved + 1 added - 1 removed
    expect(save()).toHaveTextContent("Save selection (2 changes)");

    await userEvent.click(screen.getByRole("checkbox", { name: /repo-1/ }));

    expect(save()).toHaveTextContent("Save selection (1 change)");
    await userEvent.click(screen.getByRole("checkbox", { name: /repo-2/ }));
    expect(save()).toBeDisabled();
  });

  it("saves only the changes and confirms it", async () => {
    let saved = false;
    const { fetchStub } = stubApi({
      ...auth,
      [LIST]: () => ({
        status: 200,
        body: listOf(saved ? [item(1, { is_selected: true }), item(2)] : [item(1), item(2, { is_selected: true })]),
      }),
      [SAVE]: () => {
        saved = true;
        return { status: 200, body: { selected_count: 1 } };
      },
    });
    renderPage();

    await userEvent.click(await screen.findByRole("checkbox", { name: /repo-1/ }));
    await userEvent.click(screen.getByRole("checkbox", { name: /repo-2/ }));
    await userEvent.click(screen.getByRole("button", { name: /save selection/i }));

    expect(await screen.findByText(/your selection is saved. 1 repository is selected/i)).toBeInTheDocument();
    expect(savedBody(fetchStub)).toEqual({ select: ["repo-id-1"], unselect: ["repo-id-2"] });
    expect(screen.getByRole("checkbox", { name: /repo-1/ })).toBeChecked();
    expect(screen.getByRole("button", { name: "Save selection" })).toBeDisabled();
  });

  it("keeps my choices and says so when saving fails, then lets me try again", async () => {
    let attempts = 0;
    stubApi({
      ...auth,
      [LIST]: { status: 200, body: listOf([item(1), item(2)]) },
      [SAVE]: () => (++attempts === 1 ? { status: 500 } : { status: 200, body: { selected_count: 1 } }),
    });
    renderPage();
    await userEvent.click(await screen.findByRole("checkbox", { name: /repo-1/ }));

    await userEvent.click(screen.getByRole("button", { name: /save selection/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Your choices are kept");
    expect(screen.getByRole("checkbox", { name: /repo-1/ })).toBeChecked();

    await userEvent.click(screen.getByRole("button", { name: /save selection/i }));

    expect(await screen.findByText(/your selection is saved/i)).toBeInTheDocument();
  });

  it("keeps my choices when DevPulse cannot be reached", async () => {
    stubApi({
      ...auth,
      [LIST]: { status: 200, body: listOf([item(1)]) },
      [SAVE]: "network-error",
    });
    renderPage();
    await userEvent.click(await screen.findByRole("checkbox", { name: /repo-1/ }));

    await userEvent.click(screen.getByRole("button", { name: /save selection/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Could not reach DevPulse");
    expect(screen.getByRole("checkbox", { name: /repo-1/ })).toBeChecked();
  });

  it("shows a repository the app can no longer access as a safe message", async () => {
    stubApi({
      ...auth,
      [LIST]: { status: 200, body: listOf([item(1)]) },
      [SAVE]: {
        status: 409,
        body: { code: "repository_unavailable", message: "DevPulse can no longer access one of the selected repositories on GitHub." },
      },
    });
    renderPage();
    await userEvent.click(await screen.findByRole("checkbox", { name: /repo-1/ }));

    await userEvent.click(screen.getByRole("button", { name: /save selection/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/can no longer access one of the selected/);
  });

  it("never shows an unknown server message", async () => {
    stubApi({
      ...auth,
      [LIST]: { status: 200, body: listOf([item(1)]) },
      [SAVE]: { status: 500, body: { code: "internal_error", message: "Traceback ghs_leaked-token" } },
    });
    renderPage();
    await userEvent.click(await screen.findByRole("checkbox", { name: /repo-1/ }));

    await userEvent.click(screen.getByRole("button", { name: /save selection/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Could not save your selection");
    expect(document.body).not.toHaveTextContent("ghs_leaked-token");
  });
});

describe("select repositories: search and pages", () => {
  it("searches by name and shows the matches", async () => {
    stubApi({
      ...auth,
      [LIST]: { status: 200, body: listOf([item(1), item(2)]) },
      [`${LIST}&q=repo-2`]: { status: 200, body: listOf([item(2)]) },
    });
    renderPage();
    await screen.findByText("alice-dev/repo-1");

    await userEvent.type(screen.getByRole("searchbox", { name: "Search repositories" }), "repo-2");

    expect(await screen.findByText(/1 matching/)).toBeInTheDocument();
    expect(screen.queryByText("alice-dev/repo-1")).not.toBeInTheDocument();
  });

  it("says when nothing matches the search", async () => {
    stubApi({
      ...auth,
      [LIST]: { status: 200, body: listOf([item(1)]) },
      [`${LIST}&q=zzz`]: { status: 200, body: listOf([]) },
    });
    renderPage();
    await screen.findByText("alice-dev/repo-1");

    await userEvent.type(screen.getByRole("searchbox", { name: "Search repositories" }), "zzz");

    expect(await screen.findByText("No repositories match “zzz”.")).toBeInTheDocument();
  });

  it("keeps unsaved choices while searching", async () => {
    stubApi({
      ...auth,
      [LIST]: { status: 200, body: listOf([item(1), item(2)]) },
      [`${LIST}&q=repo-2`]: { status: 200, body: listOf([item(2)]) },
    });
    renderPage();
    await userEvent.click(await screen.findByRole("checkbox", { name: /repo-1/ }));

    const box = screen.getByRole("searchbox", { name: "Search repositories" });
    await userEvent.type(box, "repo-2");
    await screen.findByText(/1 matching/);
    await userEvent.clear(box);

    expect(await screen.findByRole("checkbox", { name: /repo-1/ })).toBeChecked();
    expect(screen.getByRole("button", { name: /save selection \(1 change\)/i })).toBeInTheDocument();
  });

  it("moves between pages and keeps unsaved choices", async () => {
    const page1 = Array.from({ length: 2 }, (_, n) => item(n + 1));
    stubApi({
      ...auth,
      [LIST]: { status: 200, body: listOf(page1, { total: 120 }) },
      "GET /api/repositories?page=2&page_size=50": {
        status: 200,
        body: listOf([item(51)], { total: 120, page: 2 }),
      },
    });
    renderPage();
    await userEvent.click(await screen.findByRole("checkbox", { name: /repo-1$/ }));
    expect(screen.getByText("Page 1 of 3")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Previous" })).toBeDisabled();

    await userEvent.click(screen.getByRole("button", { name: "Next" }));

    expect(await screen.findByText("alice-dev/repo-51")).toBeInTheDocument();
    expect(screen.getByText("Page 2 of 3")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /save selection \(1 change\)/i })).toBeInTheDocument();
  });
});

describe("select repositories: safety", () => {
  it("keeps credentials out of the page and out of browser storage", async () => {
    stubApi({ ...auth, [LIST]: { status: 200, body: listOf([item(1, { is_selected: true })]) } });
    renderPage();
    const page = await screen.findByRole("list", { name: "Repositories" });

    expect(within(page).getAllByRole("listitem")).toHaveLength(1);
    expect(localStorage).toHaveLength(0);
    expect(sessionStorage).toHaveLength(0);
    expect(document.body.textContent).not.toMatch(/ghu_|ghs_|ghp_|bearer|installation_id/i);
  });
});
