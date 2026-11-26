import { Link } from "react-router-dom";
import { attentionReason, formatUtc } from "../../connection/utils/connectionMessages";
import type { Summary } from "../types";

type Props = { summary: Summary; gaveUp: boolean; onReload: () => void };

// Warnings sit above the data, which stays visible so it is never silently wrong.
export default function DashboardBanners({ summary, gaveUp, onReload }: Props) {
  const needsAttention = summary.connection_status === "needs_attention";
  const lastUpdated = summary.last_updated_at ? formatUtc(summary.last_updated_at) : null;
  const importing =
    summary.connection_status === "active" &&
    summary.repository_count > 0 &&
    (!summary.history_complete || summary.last_updated_at === null);

  return (
    <>
      {needsAttention && (
        <div className="banner banner-warning" role="alert">
          <span aria-hidden="true">!</span>
          <strong>GitHub needs your attention.</strong>
          <span>{attentionReason(summary.connection_reason)}</span>
          <Link className="btn btn-secondary" to="/connect">
            Review access on GitHub
          </Link>
        </div>
      )}

      {summary.is_stale && !needsAttention && (
        <p className="banner banner-warning" role="status">
          <span aria-hidden="true">!</span>
          <strong>Out of date.</strong>
          <span>
            {summary.stale_reason === "last_run_failed"
              ? "The latest update could not finish, so these numbers may be behind. DevPulse will try again automatically."
              : "These numbers have not been refreshed recently. DevPulse will keep trying."}
            {lastUpdated ? ` Showing data from ${lastUpdated}.` : ""}
          </span>
        </p>
      )}

      {importing && !gaveUp && (
        <p className="banner banner-info" role="status">
          <span aria-hidden="true">↻</span>
          {summary.history_complete
            ? "Waiting for the first update…"
            : `Importing history: ${summary.history_repositories_complete} of ${summary.history_repositories_total} repositories. Numbers will grow as it finishes.`}
        </p>
      )}

      {importing && gaveUp && (
        <div className="banner banner-warning" role="status">
          <span aria-hidden="true">!</span>
          Still importing. Reload to check again.
          <button type="button" className="btn btn-secondary" onClick={onReload}>
            Reload
          </button>
        </div>
      )}
    </>
  );
}
