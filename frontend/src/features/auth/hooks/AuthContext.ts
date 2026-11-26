import { createContext } from "react";
import type { AuthState } from "../types";

export type AuthContextValue = {
  state: AuthState;
  reload: () => void;
  signOut: () => Promise<void>;
};

export const AuthContext = createContext<AuthContextValue | null>(null);
