export type RepositoryItem = {
  id: string;
  full_name: string;
  is_private: boolean;
  is_selected: boolean;
};

export type RepositoryList = {
  list_status: "syncing" | "ready";
  refreshed_at: string | null;
  total: number;
  selected_count: number;
  page: number;
  page_size: number;
  items: RepositoryItem[];
};

export type SelectionChanges = {
  select: string[];
  unselect: string[];
};

export type SelectionResult = { selected_count: number };

export type ListState =
  | { status: "loading" }
  | { status: "ready"; data: RepositoryList }
  | { status: "not_connected" }
  | { status: "error" };
