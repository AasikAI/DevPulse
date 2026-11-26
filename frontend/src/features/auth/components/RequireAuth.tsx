import { Navigate, Outlet } from "react-router-dom";
import ErrorState from "../../../shared/components/ErrorState";
import LoadingState from "../../../shared/components/LoadingState";
import { useAuth } from "../hooks/useAuth";

export default function RequireAuth() {
  const { state, reload } = useAuth();

  switch (state.status) {
    case "loading":
      return <LoadingState label="Checking your session…" />;
    case "error":
      return (
        <ErrorState
          title="DevPulse is unavailable"
          message="We could not check your session. Please try again."
          onRetry={reload}
        />
      );
    case "unauthenticated":
      return <Navigate to="/sign-in" replace />;
    case "authenticated":
      return <Outlet />;
  }
}
