// Same-origin calls: in development Vite proxies /api to FastAPI, so the
// session cookie stays first-party and no credential is handled in JavaScript.

export class ApiError extends Error {
  readonly status: number;
  readonly code: string | null;

  constructor(status: number, code: string | null, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

type ErrorBody = { code?: unknown; message?: unknown };

async function request(path: string, init: RequestInit = {}): Promise<Response> {
  let response: Response;
  try {
    response = await fetch(path, { credentials: "same-origin", ...init });
  } catch {
    // status 0 = the backend could not be reached at all.
    throw new ApiError(0, "network_error", "Could not reach DevPulse.");
  }
  if (!response.ok) {
    let body: ErrorBody = {};
    try {
      body = (await response.json()) as ErrorBody;
    } catch {
      // Non-JSON error bodies are ignored; the status is enough.
    }
    throw new ApiError(
      response.status,
      typeof body.code === "string" ? body.code : null,
      typeof body.message === "string" ? body.message : "The request failed.",
    );
  }
  return response;
}

export async function apiGet<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await request(path, { signal });
  return (await response.json()) as T;
}

export async function apiPost(path: string): Promise<void> {
  await request(path, { method: "POST" });
}
