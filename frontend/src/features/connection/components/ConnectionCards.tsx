import { Link } from "react-router-dom";
import { INSTALL_URL } from "../api/connectionApi";
import type { Connection } from "../types";
import { attentionReason, formatUtc } from "../utils/connectionMessages";

export function NotConnectedCard() {
  return (
    <div className="setup-card">
      <p className="eyebrow">01 / Connect</p>
      <h1 className="page-title">Your next insight starts here.</h1>
      <p className="setup-lead">
        Connect your GitHub account to see the work behind your next release.
      </p>
      <div className="setup-panel">
        <strong>GitHub App integration</strong>
        <span>Read-only permissions. Revoke access at any time.</span>
      </div>
      <ul className="checklist">
        <li>
          <span aria-hidden="true">✓</span> Read-only access to repositories and pull requests
        </li>
        <li>
          <span aria-hidden="true">✓</span> Choose exactly which repositories to include
        </li>
        <li>
          <span aria-hidden="true">✓</span> No access to secrets or environment variables
        </li>
      </ul>
      <a className="btn btn-primary" href={INSTALL_URL}>
        Connect GitHub <span aria-hidden="true">→</span>
      </a>
      <p className="fine-print">You will review the requested permissions on GitHub before authorising.</p>
    </div>
  );
}

type ConnectedProps = { connection: Connection; gaveUp: boolean; onCheckAgain: () => void };

export function ConnectedCard({ connection, gaveUp, onCheckAgain }: ConnectedProps) {
  const count = connection.repository_count;
  const fetched = connection.repositories_synced_at !== null;

  return (
    <div className="setup-card">
      <p className="eyebrow">01 / Connect</p>
      <h1 className="page-title">GitHub is connected.</h1>
      <p className="banner banner-success">
        <strong>
          <span aria-hidden="true">✓</span> Connected as{" "}
          <span className="mono">@{connection.account_login}</span>
        </strong>
      </p>

      {!fetched && !gaveUp && (
        <p className="banner banner-info" role="status">
          <span aria-hidden="true">↻</span> Fetching your repositories…
        </p>
      )}
      {!fetched && gaveUp && (
        <div className="banner banner-warning" role="status">
          <span aria-hidden="true">!</span> Fetching is taking longer than expected.
          <button type="button" className="btn btn-secondary" onClick={onCheckAgain}>
            Check again
          </button>
        </div>
      )}
      {fetched && count > 0 && (
        <>
          <p className="setup-lead">
            <strong>
              {count} {count === 1 ? "repository is" : "repositories are"} available.
            </strong>{" "}
            Next, choose which ones DevPulse should track.
          </p>
          <Link className="btn btn-primary" to="/repositories">
            Select repositories <span aria-hidden="true">→</span>
          </Link>
        </>
      )}
      {fetched && count === 0 && (
        <p className="setup-lead">
          DevPulse can not see any repositories yet. Give the DevPulse GitHub App access to some on
          GitHub, then check again.
        </p>
      )}
      {fetched && (
        <button type="button" className="btn btn-secondary" onClick={onCheckAgain}>
          Check again
        </button>
      )}

      {connection.last_checked_at && (
        <p className="fine-print">Last checked: {formatUtc(connection.last_checked_at)}</p>
      )}
    </div>
  );
}

export function NeedsAttentionCard({ connection }: { connection: Connection }) {
  return (
    <div className="setup-card">
      <p className="eyebrow">01 / Connect</p>
      <h1 className="page-title">GitHub needs your attention.</h1>
      <div className="banner banner-warning" role="alert">
        <span aria-hidden="true">!</span>
        <span>{attentionReason(connection.reason)}</span>
      </div>
      <a className="btn btn-primary" href={INSTALL_URL}>
        Review access on GitHub <span aria-hidden="true">→</span>
      </a>
      {connection.last_checked_at && (
        <p className="fine-print">Last checked: {formatUtc(connection.last_checked_at)}</p>
      )}
    </div>
  );
}
