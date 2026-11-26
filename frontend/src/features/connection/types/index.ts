export type ConnectionStatus = "not_connected" | "active" | "needs_attention";

export type Connection = {
  status: ConnectionStatus;
  reason: string | null;
  account_login: string | null;
  connected_at: string | null;
  last_checked_at: string | null;
  repositories_synced_at: string | null;
  repository_count: number;
};

export type ConnectionState =
  | { status: "loading" }
  | { status: "ready"; connection: Connection }
  | { status: "error" };
