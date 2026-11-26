import type { Summary } from "../types";
import { plural } from "../utils/format";

type CardProps = { label: string; value: number; caption: string };

function Kpi({ label, value, caption }: CardProps) {
  return (
    <div className="kpi">
      <span className="kpi-label">{label}</span>
      <strong className="kpi-value">{value}</strong>
      <span className="kpi-caption">{caption}</span>
    </div>
  );
}

export default function KpiCards({ summary }: { summary: Summary }) {
  const { totals, weeks } = summary;
  const importing = !summary.history_complete;

  return (
    <div className="kpi-grid">
      <Kpi label="Open now" value={totals.open_now} caption="Drafts included" />
      <Kpi label="Opened" value={totals.opened_in_window} caption={`Last ${weeks} weeks`} />
      <Kpi label="Merged" value={totals.merged_in_window} caption={`Last ${weeks} weeks`} />
      <Kpi
        label="Selected repositories"
        value={summary.repository_count}
        caption={
          importing
            ? `Importing history: ${summary.history_repositories_complete} of ${summary.history_repositories_total}`
            : `${plural(summary.history_repositories_total, "repository", "repositories")} fully imported`
        }
      />
    </div>
  );
}
