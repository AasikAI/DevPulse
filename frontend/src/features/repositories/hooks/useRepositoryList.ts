import { useCallback, useEffect, useState } from "react";
import { ApiError } from "../../../shared/api/http";
import { fetchRepositories } from "../api/repositoriesApi";
import type { ListState } from "../types";

const POLL_INTERVAL_MS = 3000;
// About a minute, then stop and let the user check again.
const MAX_POLLS = 20;

// Loads one page of repositories. While the first repository list is still being
// fetched in the background, it re-checks every few seconds for a while.
export function useRepositoryList(search: string, page: number) {
  const [state, setState] = useState<ListState>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);
  const [polls, setPolls] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    fetchRepositories({ search, page }, controller.signal)
      .then((data) => setState({ status: "ready", data }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        if (error instanceof ApiError && error.code === "not_connected") {
          setState({ status: "not_connected" });
        } else {
          setState({ status: "error" });
        }
      });
    return () => controller.abort();
  }, [search, page, attempt]);

  const syncing = state.status === "ready" && state.data.list_status === "syncing";

  useEffect(() => {
    if (!syncing || polls >= MAX_POLLS) return;
    const timer = setTimeout(() => {
      setPolls((n) => n + 1);
      setAttempt((n) => n + 1);
    }, POLL_INTERVAL_MS);
    return () => clearTimeout(timer);
  }, [syncing, polls, state]);

  // Shows the loading state again; for "Try again" and "Check again".
  const reload = useCallback(() => {
    setState({ status: "loading" });
    setPolls(0);
    setAttempt((n) => n + 1);
  }, []);

  // Fetches fresh data in the background without clearing the screen.
  const refresh = useCallback(() => setAttempt((n) => n + 1), []);

  return { state, reload, refresh, gaveUp: syncing && polls >= MAX_POLLS };
}
