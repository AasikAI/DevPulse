import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { ApiError } from "../../../shared/api/http";
import { fetchCurrentUser, logout } from "../api/authApi";
import type { AuthState } from "../types";
import { AuthContext, type AuthContextValue } from "./AuthContext";

// The session itself lives in an HTTP-only cookie. This provider only asks the
// server "who am I?" and keeps the answer in memory, never in browser storage.
export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    fetchCurrentUser(controller.signal)
      .then((user) => setState({ status: "authenticated", user }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        if (error instanceof ApiError && error.status === 401) {
          setState({ status: "unauthenticated" });
        } else {
          setState({ status: "error" });
        }
      });
    return () => controller.abort();
  }, [attempt]);

  const reload = useCallback(() => {
    setState({ status: "loading" });
    setAttempt((n) => n + 1);
  }, []);

  const signOut = useCallback(async () => {
    try {
      await logout();
    } catch (error) {
      // Already signed out on the server is the outcome we wanted anyway.
      if (!(error instanceof ApiError && error.status === 401)) throw error;
    }
    setState({ status: "unauthenticated" });
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ state, reload, signOut }),
    [state, reload, signOut],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
