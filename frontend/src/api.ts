export type HealthResponse = {
  status: "ok" | "degraded";
  app: string;
  environment: string;
  database: "up" | "down";
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

// The backend answers 503 with a valid JSON body when the DB is down,
// so a non-2xx response is still parsed instead of thrown.
export async function fetchHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE_URL}/health`, { signal });
  return (await res.json()) as HealthResponse;
}
