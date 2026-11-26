import { apiGet } from "../../../shared/api/http";
import type { Connection } from "../types";

// Full-page navigation, not fetch: the backend redirects to GitHub's install page.
export const INSTALL_URL = "/api/github/install";

export function fetchConnection(signal?: AbortSignal): Promise<Connection> {
  return apiGet<Connection>("/api/github/connection", signal);
}
