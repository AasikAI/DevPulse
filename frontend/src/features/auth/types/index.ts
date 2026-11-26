export type User = {
  id: string;
  login: string;
  name: string | null;
  avatar_url: string | null;
  email: string | null;
};

export type AuthState =
  | { status: "loading" }
  | { status: "authenticated"; user: User }
  | { status: "unauthenticated" }
  // The backend could not be reached or answered unexpectedly.
  | { status: "error" };
