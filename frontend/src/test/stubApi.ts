import { vi } from "vitest";

type Reply = { status: number; body?: unknown } | "network-error" | "pending";
type Handler = Reply | (() => Reply);

// Stubs fetch at the network boundary. Keys look like "GET /api/auth/me".
// "pending" never answers, so a loading state can be observed.
export function stubApi(routes: Record<string, Handler>) {
  const calls: string[] = [];
  const fetchStub = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const key = `${init?.method ?? "GET"} ${String(input)}`;
    calls.push(key);
    const route = routes[key];
    if (route === undefined) throw new Error(`Unexpected request: ${key}`);
    const reply = typeof route === "function" ? route() : route;
    if (reply === "pending") return new Promise<Response>(() => {});
    if (reply === "network-error") throw new TypeError("Failed to fetch");
    const noBody = reply.status === 204 || reply.body === undefined;
    return new Response(noBody ? null : JSON.stringify(reply.body), { status: reply.status });
  });
  vi.stubGlobal("fetch", fetchStub);
  return { calls, fetchStub };
}

export const aliceUser = {
  id: "7b0c3a4e-1111-2222-3333-444455556666",
  login: "alice-dev",
  name: "Alice Example",
  avatar_url: null,
  email: null,
};

export const notConnected = {
  status: "not_connected",
  reason: null,
  account_login: null,
  connected_at: null,
  last_checked_at: null,
  repositories_synced_at: null,
  repository_count: 0,
};

export function connectedAs(overrides: Record<string, unknown> = {}) {
  return {
    ...notConnected,
    status: "active",
    account_login: "alice-dev",
    connected_at: "2026-11-26T09:00:00Z",
    last_checked_at: "2026-11-26T10:30:00Z",
    repositories_synced_at: "2026-11-26T10:30:00Z",
    repository_count: 3,
    ...overrides,
  };
}
