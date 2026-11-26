import { useCallback, useEffect, useState } from "react";
import { fetchSummary } from "../api/dashboardApi";
import type { DashboardState, Summary } from "../types";

const POLL_INTERVAL_MS = 30_000;
// Five minutes of checking, then stop and let the user reload.
const MAX_POLLS = 10;

// Data is still on its way while repositories are selected but their history import has
// not finished, or nothing has been fetched at all yet.
export function isIncomplete(summary: Summary): boolean {
  return (
    summary.connection_status === "active" &&
    summary.repository_count > 0 &&
    (!summary.history_complete || summary.last_updated_at === null)
  );
}

// Loads the dashboard numbers from DevPulse's own API (never GitHub). While the first
// import is still running it re-checks every 30 seconds, for up to five minutes.
export function useDashboard(weeks: number) {
  const [state, setState] = useState<DashboardState>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);
  const [polls, setPolls] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    fetchSummary(weeks, controller.signal)
      .then((summary) => setState({ status: "ready", summary }))
      .catch(() => {
        if (!controller.signal.aborted) setState({ status: "error" });
      });
    return () => controller.abort();
  }, [weeks, attempt]);

  const incomplete = state.status === "ready" && isIncomplete(state.summary);

  useEffect(() => {
    if (!incomplete || polls >= MAX_POLLS) return;
    const timer = setTimeout(() => {
      setPolls((n) => n + 1);
      setAttempt((n) => n + 1);
    }, POLL_INTERVAL_MS);
    return () => clearTimeout(timer);
  }, [incomplete, polls, state]);

  // Shows the loading state again; for "Try again" and "Reload".
  const reload = useCallback(() => {
    setState({ status: "loading" });
    setPolls(0);
    setAttempt((n) => n + 1);
  }, []);

  return { state, reload, gaveUp: incomplete && polls >= MAX_POLLS };
}
