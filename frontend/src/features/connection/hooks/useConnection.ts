import { useCallback, useEffect, useState } from "react";
import { fetchConnection } from "../api/connectionApi";
import type { ConnectionState } from "../types";

const POLL_INTERVAL_MS = 3000;
// About a minute, then stop and let the user check again.
const MAX_POLLS = 20;

// Loads the connection status. While the first repository list is still being
// fetched in the background, it re-checks every few seconds for a while.
export function useConnection() {
  const [state, setState] = useState<ConnectionState>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);
  const [polls, setPolls] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    fetchConnection(controller.signal)
      .then((connection) => setState({ status: "ready", connection }))
      .catch(() => {
        if (!controller.signal.aborted) setState({ status: "error" });
      });
    return () => controller.abort();
  }, [attempt]);

  const fetching =
    state.status === "ready" &&
    state.connection.status === "active" &&
    state.connection.repositories_synced_at === null;

  useEffect(() => {
    if (!fetching || polls >= MAX_POLLS) return;
    const timer = setTimeout(() => {
      setPolls((n) => n + 1);
      setAttempt((n) => n + 1);
    }, POLL_INTERVAL_MS);
    return () => clearTimeout(timer);
  }, [fetching, polls, state]);

  const reload = useCallback(() => {
    setState({ status: "loading" });
    setPolls(0);
    setAttempt((n) => n + 1);
  }, []);

  return { state, reload, gaveUp: fetching && polls >= MAX_POLLS };
}
