import { useSearchParams } from "react-router-dom";
import LogoutButton from "../../auth/components/LogoutButton";
import ErrorState from "../../../shared/components/ErrorState";
import LoadingState from "../../../shared/components/LoadingState";
import SetupLayout from "../../../shared/components/SetupLayout";
import { ConnectedCard, NeedsAttentionCard, NotConnectedCard } from "../components/ConnectionCards";
import { useConnection } from "../hooks/useConnection";
import { connectErrorMessage } from "../utils/connectionMessages";

export default function ConnectGitHubPage() {
  const { state, reload, gaveUp } = useConnection();
  const [params] = useSearchParams();
  const errorMessage = connectErrorMessage(params.get("error"));

  return (
    <SetupLayout crumb="Setup" action={<LogoutButton className="btn btn-ghost" />}>
      {state.status === "loading" && <LoadingState label="Checking your GitHub connection…" />}
      {state.status === "error" && (
        <ErrorState
          title="Could not load your GitHub connection"
          message="DevPulse could not check your connection. Please try again."
          onRetry={reload}
        />
      )}
      {state.status === "ready" && (
        <div className="setup-grid">
          <section className="setup-intro">
            <h2>A clearer view of your engineering.</h2>
            <p>One secure connection. Your pull request activity, from the repositories you choose.</p>
            <ol className="steps" aria-label="Setup steps">
              <li className="step step-current" aria-current="step">
                <span>01</span> Connect GitHub
              </li>
              <li className="step">
                <span>02</span> Select repositories
              </li>
            </ol>
            <p className="fine-print">
              READ-ONLY BY DEFAULT
              <br />
              Your source code stays on GitHub.
            </p>
          </section>

          <div className="setup-column">
            {errorMessage && (
              <p className="banner banner-danger" role="alert">
                <span aria-hidden="true">×</span> {errorMessage}
              </p>
            )}
            {state.connection.status === "not_connected" && <NotConnectedCard />}
            {state.connection.status === "active" && (
              <ConnectedCard connection={state.connection} gaveUp={gaveUp} onCheckAgain={reload} />
            )}
            {state.connection.status === "needs_attention" && (
              <NeedsAttentionCard connection={state.connection} />
            )}
          </div>
        </div>
      )}
    </SetupLayout>
  );
}
