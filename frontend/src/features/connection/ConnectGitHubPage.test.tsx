import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "../../App";
import { AuthProvider } from "../auth/hooks/AuthProvider";
import { aliceUser, connectedAs, notConnected, stubApi } from "../../test/stubApi";

function renderConnect(path = "/connect") {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <AuthProvider>
        <App />
      </AuthProvider>
    </MemoryRouter>,
  );
}

const auth = { "GET /api/auth/me": { status: 200, body: aliceUser } };
const connection = (body: unknown, status = 200) => ({
  ...auth,
  "GET /api/github/connection": { status, body },
});

afterEach(() => {
  vi.useRealTimers();
});

describe("connect GitHub page: not connected", () => {
  it("offers Connect GitHub, which starts the install on the backend", async () => {
    stubApi(connection(notConnected));
    renderConnect();

    const link = await screen.findByRole("link", { name: /connect github/i });

    expect(link).toHaveAttribute("href", "/api/github/install");
    expect(screen.getByRole("heading", { name: "Your next insight starts here." })).toBeInTheDocument();
    expect(screen.getByText(/read-only access to repositories and pull requests/i)).toBeInTheDocument();
  });

  it("shows a loading state while the connection is being checked", async () => {
    stubApi({ ...auth, "GET /api/github/connection": "pending" });
    renderConnect();

    expect(await screen.findByText("Checking your GitHub connection…")).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Your next insight starts here." })).not.toBeInTheDocument();
  });

  it("shows an error with a retry when the connection cannot be loaded", async () => {
    let attempts = 0;
    stubApi({
      ...auth,
      "GET /api/github/connection": () =>
        ++attempts === 1 ? { status: 500 } : { status: 200, body: notConnected },
    });
    renderConnect();

    expect(await screen.findByRole("alert")).toHaveTextContent("Could not load your GitHub connection");
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));

    expect(await screen.findByRole("heading", { name: "Your next insight starts here." })).toBeInTheDocument();
  });
});

describe("connect GitHub page: connected", () => {
  it("shows that GitHub is connected and how many repositories are available", async () => {
    stubApi(connection(connectedAs()));
    renderConnect();

    expect(await screen.findByRole("heading", { name: "GitHub is connected." })).toBeInTheDocument();
    expect(screen.getByText("@alice-dev")).toBeInTheDocument();
    expect(screen.getByText(/3 repositories are available/)).toBeInTheDocument();
    expect(screen.getByText("Last checked: 26 Nov 2026, 10:30 UTC")).toBeInTheDocument();
  });

  it("leads on to choosing repositories once they are available", async () => {
    stubApi(connection(connectedAs()));
    renderConnect();

    expect(await screen.findByRole("link", { name: /select repositories/i })).toHaveAttribute(
      "href",
      "/repositories",
    );
  });

  it("does not offer to choose repositories while they are still being fetched", async () => {
    stubApi(connection(connectedAs({ repositories_synced_at: null, repository_count: 0 })));
    renderConnect();
    await screen.findByText("Fetching your repositories…");

    expect(screen.queryByRole("link", { name: /select repositories/i })).not.toBeInTheDocument();
  });

  it("uses the singular for one repository", async () => {
    stubApi(connection(connectedAs({ repository_count: 1 })));
    renderConnect();

    expect(await screen.findByText(/1 repository is available/)).toBeInTheDocument();
  });

  it("says so when the app can not see any repositories yet", async () => {
    stubApi(connection(connectedAs({ repository_count: 0 })));
    renderConnect();

    expect(await screen.findByText(/can not see any repositories yet/)).toBeInTheDocument();
  });

  it("says the repositories are being fetched until the background job has run", async () => {
    stubApi(connection(connectedAs({ repositories_synced_at: null, repository_count: 0 })));
    renderConnect();

    expect(await screen.findByText("Fetching your repositories…")).toBeInTheDocument();
    expect(screen.queryByText(/repositories are available/)).not.toBeInTheDocument();
  });

  it("keeps checking while repositories are fetched and then shows them", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    let calls = 0;
    stubApi({
      ...auth,
      "GET /api/github/connection": () =>
        ++calls < 2
          ? { status: 200, body: connectedAs({ repositories_synced_at: null, repository_count: 0 }) }
          : { status: 200, body: connectedAs() },
    });
    renderConnect();
    expect(await screen.findByText("Fetching your repositories…")).toBeInTheDocument();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(3100);
    });

    expect(await screen.findByText(/3 repositories are available/)).toBeInTheDocument();
  });

  it("stops checking after a while and offers to check again", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    stubApi(connection(connectedAs({ repositories_synced_at: null, repository_count: 0 })));
    renderConnect();
    await screen.findByText("Fetching your repositories…");

    // One poll per tick; each tick is flushed so the next timer gets scheduled.
    for (let tick = 0; tick < 21; tick++) {
      await act(async () => {
        await vi.advanceTimersByTimeAsync(3100);
      });
    }

    expect(await screen.findByText(/taking longer than expected/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Check again" })).toBeInTheDocument();
  });
});

describe("connect GitHub page: needs attention", () => {
  it.each([
    ["access_revoked", /can no longer access your GitHub account/],
    ["permission_missing", /missing a read permission/],
    ["suspended", /suspended on your GitHub account/],
  ])("explains %s and offers a way to fix it on GitHub", async (reason, message) => {
    stubApi(connection(connectedAs({ status: "needs_attention", reason })));
    renderConnect();

    expect(await screen.findByRole("heading", { name: "GitHub needs your attention." })).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent(message);
    expect(screen.getByRole("link", { name: /review access on github/i })).toHaveAttribute(
      "href",
      "/api/github/install",
    );
  });

  it("falls back to a generic message for an unknown reason", async () => {
    stubApi(connection(connectedAs({ status: "needs_attention", reason: "something_new" })));
    renderConnect();

    expect(await screen.findByRole("alert")).toHaveTextContent("could not use your GitHub connection");
  });
});

describe("connect GitHub page: errors from the install redirect", () => {
  it.each([
    ["installation_not_allowed", /could not be connected/],
    ["invalid_state", /invalid or had already been used/],
    ["github_unavailable", /not responding/],
    ["not_configured", /not set up/],
    ["failed", /failed/],
  ])("shows a safe message for %s and keeps the connect button", async (code, message) => {
    stubApi(connection(notConnected));
    renderConnect(`/connect?error=${code}`);

    expect(await screen.findByRole("alert")).toHaveTextContent(message);
    expect(screen.getByRole("link", { name: /connect github/i })).toBeInTheDocument();
  });

  it("never shows text taken from the URL", async () => {
    stubApi(connection(notConnected));
    renderConnect("/connect?error=<b>ghs_secret-123</b>");

    expect(await screen.findByRole("alert")).toHaveTextContent(/failed/i);
    expect(document.body).not.toHaveTextContent("ghs_secret-123");
  });
});

describe("connect GitHub page: safety", () => {
  it("keeps credentials and installation details out of the page and browser storage", async () => {
    stubApi(connection(connectedAs()));
    renderConnect();
    await screen.findByRole("heading", { name: "GitHub is connected." });

    expect(localStorage).toHaveLength(0);
    expect(sessionStorage).toHaveLength(0);
    expect(document.body.textContent).not.toMatch(/ghu_|ghs_|ghp_|bearer|installation_id/i);
  });
});
