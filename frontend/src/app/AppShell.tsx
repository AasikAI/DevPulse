import { useState } from "react";
import { Outlet } from "react-router-dom";
import { useAuth } from "../features/auth/hooks/useAuth";

// The signed-in layout. Navigation links are added with the pages they point to.
export default function AppShell() {
  const { state, signOut } = useAuth();
  const [logoutFailed, setLogoutFailed] = useState(false);

  async function handleLogout() {
    setLogoutFailed(false);
    try {
      await signOut();
    } catch {
      setLogoutFailed(true);
    }
  }

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="logo">DevPulse</div>
        {state.status === "authenticated" && (
          <div className="sidebar-account">
            <span>Signed in as</span>
            <strong className="mono">@{state.user.login}</strong>
            <button type="button" className="btn btn-secondary" onClick={handleLogout}>
              Log out
            </button>
            {logoutFailed && (
              <p role="alert">Could not log out. Please try again.</p>
            )}
          </div>
        )}
      </aside>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
