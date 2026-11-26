import { Suspense, lazy } from "react";
import type { Summary } from "../types";
import { formatWeek, plural } from "../utils/format";

const WeeklyChart = lazy(() => import("./WeeklyChart"));

export default function PullRequestWidget({ summary }: { summary: Summary }) {
  const { weekly, weeks, totals, repository_count: repositories } = summary;
  const hasActivity = totals.opened_in_window + totals.merged_in_window > 0;
  const lastIndex = weekly.length - 1;

  return (
    <section className="card widget" aria-labelledby="widget-title">
      <div className="widget-head">
        <h2 id="widget-title">Pull requests per week</h2>
        <p className="widget-scope">
          {plural(repositories, "selected repository", "selected repositories")} · last {weeks}{" "}
          weeks · weeks start Monday, UTC
        </p>
      </div>

      {hasActivity ? (
        <>
          <div
            role="img"
            aria-label={`Bar chart of pull requests opened and merged per week over the last ${weeks} weeks. ${totals.opened_in_window} opened and ${totals.merged_in_window} merged in total. The same numbers are in the table below.`}
          >
            <Suspense fallback={<div className="chart-canvas chart-loading">Loading chart…</div>}>
              <WeeklyChart weekly={weekly} />
            </Suspense>
          </div>
          <details className="chart-table">
            <summary>View as a table</summary>
            <table>
              <caption className="visually-hidden">
                Pull requests opened and merged per week, last {weeks} weeks
              </caption>
              <thead>
                <tr>
                  <th scope="col">Week starting (UTC)</th>
                  <th scope="col">Opened</th>
                  <th scope="col">Merged</th>
                </tr>
              </thead>
              <tbody>
                {weekly.map((week, index) => (
                  <tr key={week.week_start}>
                    <th scope="row">
                      {formatWeek(week.week_start)}
                      {index === lastIndex && " (this week, in progress)"}
                    </th>
                    <td>{week.opened}</td>
                    <td>{week.merged}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </details>
        </>
      ) : (
        <p className="widget-empty">
          {summary.history_complete
            ? `No pull requests were opened or merged in the last ${weeks} weeks.`
            : "Waiting for the first import to bring in pull requests."}
        </p>
      )}
    </section>
  );
}
