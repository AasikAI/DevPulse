import type { ReviewStateCounts } from "../types";

const ROWS: { key: keyof ReviewStateCounts; label: string }[] = [
  { key: "approved", label: "Approved" },
  { key: "changes_requested", label: "Changes requested" },
  { key: "commented", label: "Commented" },
  { key: "none", label: "No reviews yet" },
  { key: "not_loaded", label: "Review state not loaded yet" },
];

export default function ReviewStateCard({ counts }: { counts: ReviewStateCounts }) {
  return (
    <section className="card" aria-labelledby="review-title">
      <h2 id="review-title">Open pull requests by review state</h2>
      <dl className="review-list">
        {ROWS.map(({ key, label }) => (
          <div key={key} className="review-row">
            <dt>{label}</dt>
            <dd>{counts[key]}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
