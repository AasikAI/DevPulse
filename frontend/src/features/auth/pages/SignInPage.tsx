import { Navigate, useSearchParams } from "react-router-dom";
import ErrorState from "../../../shared/components/ErrorState";
import LoadingState from "../../../shared/components/LoadingState";
import { SIGN_IN_URL } from "../api/authApi";
import { useAuth } from "../hooks/useAuth";
import { signInErrorMessage } from "../utils/signInErrors";

export default function SignInPage() {
  const { state, reload } = useAuth();
  const [params] = useSearchParams();
  const errorMessage = signInErrorMessage(params.get("error"));

  if (state.status === "loading") return <LoadingState label="Checking your session…" />;
  if (state.status === "authenticated") return <Navigate to="/start" replace />;
  if (state.status === "error") {
    return (
      <ErrorState
        title="DevPulse is unavailable"
        message="We could not reach DevPulse. Please try again."
        onRetry={reload}
      />
    );
  }

  return (
    <main className="auth-page">
      <div className="card auth-card">
        <h1 className="page-title">Sign in to DevPulse</h1>
        <p>Continue with your GitHub account. DevPulse only reads your public profile to sign you in.</p>
        {errorMessage && (
          <p className="alert" role="alert">
            {errorMessage}
          </p>
        )}
        <a className="btn btn-primary" href={SIGN_IN_URL}>
          Continue with GitHub
        </a>
      </div>
    </main>
  );
}
