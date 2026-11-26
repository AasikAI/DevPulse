import { useState } from "react";
import ErrorState from "../../../shared/components/ErrorState";
import LoadingState from "../../../shared/components/LoadingState";
import { formatUtc } from "../../connection/utils/connectionMessages";
import DashboardBanners from "../components/DashboardBanners";
import { ConnectPrompt, SelectRepositoriesPrompt } from "../components/DashboardPrompts";
import KpiCards from "../components/KpiCards";
import PullRequestWidget from "../components/PullRequestWidget";
import ReviewStateCard from "../components/ReviewStateCard";
import { useDashboard } from "../hooks/useDashboard";
import { DEFAULT_WEEKS, WINDOW_OPTIONS, type WindowWeeks } from "../types";
import { plural } from "../utils/format";

export default function DashboardPage() {
  const [weeks, setWeeks] = useState<WindowWeeks>(DEFAULT_WEEKS);
  const { state, reload, gaveUp } = useDashboard(weeks);

  if (state.status === "loading") return <LoadingState label="Loading your pull requests…" />;
  if (state.status === "error") {
    return (
      <ErrorState
        title="Could not load the dashboard"
        message="DevPulse could not load your pull request data. Please try again."
        onRetry={reload}
      />
    );
  }

  const { summary } = state;
  const connected = summary.connection_status !== "not_connected";
  const tracking = connected && summary.repository_count > 0;

  return (
    <div className="content">
      <header className="page-header">
        <div>
          <h1 className="page-title">Pull requests</h1>
          <p className="page-subtitle">
            {tracking
              ? `Pull request activity across your ${plural(summary.repository_count, "selected repository", "selected repositories")}.`
              : "Pull request activity from the repositories you choose."}
          </p>
        </div>
        {tracking && (
          <div className="field-inline">
            <label htmlFor="window">Time window</label>
            <select
              id="window"
              className="select"
              value={weeks}
              onChange={(event) => setWeeks(Number(event.target.value) as WindowWeeks)}
            >
              {WINDOW_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  Last {option} weeks
                </option>
              ))}
            </select>
          </div>
        )}
      </header>

      {!connected && <ConnectPrompt />}
      {connected && <DashboardBanners summary={summary} gaveUp={gaveUp} onReload={reload} />}
      {connected && !tracking && <SelectRepositoriesPrompt />}

      {tracking && (
        <>
          <KpiCards summary={summary} />
          <div className="dashboard-grid">
            <PullRequestWidget summary={summary} />
            <ReviewStateCard counts={summary.open_by_review_state} />
          </div>
          <p className="footnote">
            {summary.last_updated_at
              ? `Last updated ${formatUtc(summary.last_updated_at)}`
              : "Not updated yet"}{" "}
            · Data comes from DevPulse’s database, not live from GitHub · Times shown in UTC · Counts
            show activity volume only
          </p>
        </>
      )}
    </div>
  );
}
