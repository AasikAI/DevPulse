import { apiGet, apiPostJson } from "../../../shared/api/http";
import type { RepositoryList, SelectionChanges, SelectionResult } from "../types";

export const PAGE_SIZE = 50;

export function fetchRepositories(
  query: { search: string; page: number },
  signal?: AbortSignal,
): Promise<RepositoryList> {
  const params = new URLSearchParams({ page: String(query.page), page_size: String(PAGE_SIZE) });
  if (query.search) params.set("q", query.search);
  return apiGet<RepositoryList>(`/api/repositories?${params.toString()}`, signal);
}

export function saveSelection(changes: SelectionChanges): Promise<SelectionResult> {
  return apiPostJson<SelectionResult>("/api/repositories/selection", changes);
}
