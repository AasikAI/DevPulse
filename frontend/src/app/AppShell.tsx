import { useState } from "react";
import { Link, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../features/auth/hooks/useAuth";
import Logo from "../shared/components/Logo";

// Breadcrumb labels per route; each new page adds its own entry.
const PAGE_LABELS: Record<string, string> = {
  "/start": "Getting started",
};

// The signed-in layout (design mockup 07). Navigation links are added with the pages they point to.
export default function AppShell() {
  const { state, signOut } = useAuth();
  const { pathname } = useLocation();
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
        <Link to="/start" className="logo-link" aria-label="DevPulse home">
          <Logo tone="light" />
        </Link>
        {state.status === "authenticated" && (
          <>
            <div className="sidebar-workspace">
              <span className="sidebar-eyebrow">Signed in as</span>
              <strong className="mono">@{state.user.login}</strong>
            </div>
            <div className="sidebar-footer">
              <button type="button" className="sidebar-action" onClick={handleLogout}>
                Log out
              </button>
              {logoutFailed && <p role="alert">Could not log out. Please try again.</p>}
            </div>
          </>
        )}
      </aside>
      <div className="main">
        <header className="topbar">
          <span>DevPulse / {PAGE_LABELS[pathname] ?? "Home"}</span>
        </header>
        <Outlet />
      </div>
    </div>
  );
}
