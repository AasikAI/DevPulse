import { apiGet, apiPost } from "../../../shared/api/http";
import type { User } from "../types";

// Full-page navigation, not fetch: the backend answers with a redirect to GitHub.
export const SIGN_IN_URL = "/api/auth/github/login";

export function fetchCurrentUser(signal?: AbortSignal): Promise<User> {
  return apiGet<User>("/api/auth/me", signal);
}

export function logout(): Promise<void> {
  return apiPost("/api/auth/logout");
}
