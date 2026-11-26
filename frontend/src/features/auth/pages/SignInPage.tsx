import { Navigate, useSearchParams } from "react-router-dom";
import ErrorState from "../../../shared/components/ErrorState";
import LoadingState from "../../../shared/components/LoadingState";
import { SIGN_IN_URL } from "../api/authApi";
import SetupLayout from "../components/SetupLayout";
import { useAuth } from "../hooks/useAuth";
import { signInErrorMessage } from "../utils/signInErrors";

export default function SignInPage() {
  const { state, reload } = useAuth();
  const [params] = useSearchParams();
  const errorMessage = signInErrorMessage(params.get("error"));

  if (state.status === "authenticated") return <Navigate to="/start" replace />;

  if (state.status === "loading") {
    return (
      <SetupLayout>
        <LoadingState label="Checking your session…" />
      </SetupLayout>
    );
  }

  if (state.status === "error") {
    return (
      <SetupLayout>
        <ErrorState
          title="DevPulse is unavailable"
          message="We could not reach DevPulse. Please try again."
          onRetry={reload}
        />
      </SetupLayout>
    );
  }

  return (
    <SetupLayout>
      <div className="setup-grid">
        <section className="setup-intro">
          <h2>A clearer view of your engineering.</h2>
          <p>Sign in once. Your pull request activity, from the repositories you choose, in one place.</p>
        </section>

        <div className="setup-card">
          <p className="eyebrow">01 / Sign in</p>
          <h1 className="page-title">Sign in to DevPulse</h1>
          <p className="setup-lead">Continue with your GitHub account to see the work behind your next release.</p>

          {errorMessage && (
            <p className="banner banner-danger" role="alert">
              <span aria-hidden="true">×</span> {errorMessage}
            </p>
          )}

          <div className="setup-panel">
            <strong>GitHub account</strong>
            <span>DevPulse reads your public GitHub profile to sign you in.</span>
          </div>

          <ul className="checklist">
            <li>
              <span aria-hidden="true">✓</span> Your GitHub sign-in token is never stored
            </li>
            <li>
              <span aria-hidden="true">✓</span> Connecting repositories is a separate, read-only step
            </li>
          </ul>

          <a className="btn btn-primary" href={SIGN_IN_URL}>
            Continue with GitHub <span aria-hidden="true">→</span>
          </a>
          <p className="fine-print">You will be sent to GitHub to authorise, then back here.</p>
        </div>
      </div>
    </SetupLayout>
  );
}
