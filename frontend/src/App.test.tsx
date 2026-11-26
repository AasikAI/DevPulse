import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import App from "./App";
import { AuthProvider } from "./features/auth/hooks/AuthProvider";
import { aliceUser, stubApi } from "./test/stubApi";

function renderApp(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <AuthProvider>
        <App />
      </AuthProvider>
    </MemoryRouter>,
  );
}

const signedOut = { "GET /api/auth/me": { status: 401, body: { code: "not_authenticated" } } };
const signedIn = { "GET /api/auth/me": { status: 200, body: aliceUser } };

describe("sign-in page", () => {
  it("offers Continue with GitHub, which starts the backend sign-in", async () => {
    stubApi(signedOut);
    renderApp("/sign-in");

    const link = await screen.findByRole("link", { name: "Continue with GitHub" });

    expect(link).toHaveAttribute("href", "/api/auth/github/login");
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("shows a loading state while the session is being checked", async () => {
    stubApi(signedOut);
    renderApp("/sign-in");

    expect(screen.getByRole("status")).toHaveTextContent("Checking your session");
    expect(await screen.findByRole("heading", { name: "Sign in to DevPulse" })).toBeInTheDocument();
  });

  it.each([
    ["cancelled", /cancelled/i],
    ["invalid_state", /invalid or had already been used/i],
    ["github_unavailable", /not responding/i],
    ["failed", /sign-in failed/i],
  ])("shows a safe message when sign-in ends with %s and lets me try again", async (code, message) => {
    stubApi(signedOut);
    renderApp(`/sign-in?error=${code}`);

    expect(await screen.findByRole("alert")).toHaveTextContent(message);
    expect(screen.getByRole("link", { name: "Continue with GitHub" })).toBeInTheDocument();
  });

  it("never shows text taken from the URL", async () => {
    stubApi(signedOut);
    renderApp("/sign-in?error=<b>secret-token-123</b>");

    const alert = await screen.findByRole("alert");

    expect(alert).toHaveTextContent(/sign-in failed/i);
    expect(document.body).not.toHaveTextContent("secret-token-123");
  });

  it("shows an error with a retry when the backend cannot be reached", async () => {
    let attempts = 0;
    stubApi({
      "GET /api/auth/me": () => (++attempts === 1 ? "network-error" : { status: 401 }),
    });
    renderApp("/sign-in");

    expect(await screen.findByRole("alert")).toHaveTextContent("DevPulse is unavailable");
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));

    expect(await screen.findByRole("heading", { name: "Sign in to DevPulse" })).toBeInTheDocument();
  });

  it("sends an already signed-in user to the start page", async () => {
    stubApi(signedIn);
    renderApp("/sign-in");

    expect(await screen.findByRole("heading", { name: "You are signed in" })).toBeInTheDocument();
  });
});

describe("protected pages", () => {
  it("sends a signed-out visitor to the sign-in page", async () => {
    stubApi(signedOut);
    renderApp("/start");

    expect(await screen.findByRole("heading", { name: "Sign in to DevPulse" })).toBeInTheDocument();
  });

  it("restores the session after a browser refresh", async () => {
    const { calls } = stubApi(signedIn);
    const first = renderApp("/start");
    expect(await screen.findByText(/Welcome, Alice Example/)).toBeInTheDocument();
    first.unmount();

    renderApp("/start");

    expect(await screen.findByText(/Welcome, Alice Example/)).toBeInTheDocument();
    expect(calls.filter((c) => c === "GET /api/auth/me")).toHaveLength(2);
  });

  it("shows an error with a retry when the session check fails", async () => {
    let attempts = 0;
    stubApi({
      "GET /api/auth/me": () => (++attempts === 1 ? { status: 500 } : { status: 200, body: aliceUser }),
    });
    renderApp("/start");

    expect(await screen.findByRole("alert")).toHaveTextContent("DevPulse is unavailable");
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));

    expect(await screen.findByText(/Welcome, Alice Example/)).toBeInTheDocument();
  });

  it("keeps credentials out of the page and out of browser storage", async () => {
    stubApi(signedIn);
    renderApp("/start");
    await screen.findByText(/Welcome, Alice Example/);

    expect(localStorage).toHaveLength(0);
    expect(sessionStorage).toHaveLength(0);
    expect(document.body.textContent).not.toMatch(/token|secret|devpulse_session/i);
  });
});

describe("logging out", () => {
  it("ends the session and returns to the sign-in page", async () => {
    const { calls } = stubApi({
      ...signedIn,
      "POST /api/auth/logout": { status: 204 },
    });
    renderApp("/start");

    await userEvent.click(await screen.findByRole("button", { name: "Log out" }));

    expect(await screen.findByRole("heading", { name: "Sign in to DevPulse" })).toBeInTheDocument();
    expect(calls).toContain("POST /api/auth/logout");
  });

  it("still signs me out locally when the server says the session had already ended", async () => {
    stubApi({ ...signedIn, "POST /api/auth/logout": { status: 401 } });
    renderApp("/start");

    await userEvent.click(await screen.findByRole("button", { name: "Log out" }));

    expect(await screen.findByRole("heading", { name: "Sign in to DevPulse" })).toBeInTheDocument();
  });

  it("stays signed in and says so when logging out fails", async () => {
    stubApi({ ...signedIn, "POST /api/auth/logout": { status: 500 } });
    renderApp("/start");

    await userEvent.click(await screen.findByRole("button", { name: "Log out" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Could not log out");
    expect(screen.getByText(/Welcome, Alice Example/)).toBeInTheDocument();
  });
});

describe("landing page", () => {
  it("sends visitors to sign-in", async () => {
    stubApi(signedOut);
    renderApp("/");

    const [cta] = await screen.findAllByRole("link", { name: /get started/i });

    expect(cta).toHaveAttribute("href", "/sign-in");
  });
});
