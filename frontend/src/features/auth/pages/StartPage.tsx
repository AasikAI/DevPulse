import { Navigate } from "react-router-dom";
import ErrorState from "../../../shared/components/ErrorState";
import LoadingState from "../../../shared/components/LoadingState";
import { useConnection } from "../../connection/hooks/useConnection";

// Where sign-in lands. A user without a connection goes to the connect page; a user with
// one (even one that needs attention, or with nothing selected) goes to the dashboard,
// which explains what to do next.
export default function StartPage() {
  const { state, reload } = useConnection();

  if (state.status === "loading") return <LoadingState label="Checking your GitHub connection…" />;
  if (state.status === "error") {
    return (
      <ErrorState
        title="Could not load your GitHub connection"
        message="DevPulse could not check your connection. Please try again."
        onRetry={reload}
      />
    );
  }
  const target = state.connection.status === "not_connected" ? "/connect" : "/dashboard";
  return <Navigate to={target} replace />;
}
