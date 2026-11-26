import { apiGet } from "../../../shared/api/http";
import type { Summary } from "../types";

export function fetchSummary(weeks: number, signal?: AbortSignal): Promise<Summary> {
  return apiGet<Summary>(`/api/pull-requests/summary?weeks=${weeks}`, signal);
}
