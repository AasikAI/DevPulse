import { apiGet } from "./http";

export type HealthResponse = {
  status: "ok" | "degraded";
  app: string;
  environment: string;
  database: "up" | "down";
};

export function fetchHealth(signal?: AbortSignal): Promise<HealthResponse> {
  return apiGet<HealthResponse>("/health", signal);
}
