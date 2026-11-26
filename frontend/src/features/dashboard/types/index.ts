export type StaleReason = "last_run_failed" | "not_updated_recently";

export type WeeklyCount = {
  // The Monday (UTC) of the week, as YYYY-MM-DD.
  week_start: string;
  opened: number;
  merged: number;
};

export type ReviewStateCounts = {
  none: number;
  commented: number;
  approved: number;
  changes_requested: number;
  not_loaded: number;
};

export type Summary = {
  connection_status: "not_connected" | "active" | "needs_attention";
  connection_reason: string | null;
  repository_count: number;
  weeks: number;
  window_start: string;
  last_updated_at: string | null;
  is_stale: boolean;
  stale_reason: StaleReason | null;
  history_complete: boolean;
  history_repositories_total: number;
  history_repositories_complete: number;
  totals: { open_now: number; opened_in_window: number; merged_in_window: number };
  open_by_review_state: ReviewStateCounts;
  weekly: WeeklyCount[];
};

export const WINDOW_OPTIONS = [4, 12, 26, 52] as const;
export type WindowWeeks = (typeof WINDOW_OPTIONS)[number];
export const DEFAULT_WEEKS: WindowWeeks = 12;

export type DashboardState =
  | { status: "loading" }
  | { status: "ready"; summary: Summary }
  | { status: "error" };
