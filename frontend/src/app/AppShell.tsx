import { NavLink, Outlet, useLocation, Link } from "react-router-dom";
import LogoutButton from "../features/auth/components/LogoutButton";
import { useAuth } from "../features/auth/hooks/useAuth";
import { useConnection } from "../features/connection/hooks/useConnection";
import Logo from "../shared/components/Logo";

// Breadcrumb labels per route; each new page adds its own entry.
const PAGE_LABELS: Record<string, string> = {
  "/dashboard": "Overview",
};

const NAV_ITEMS = [
  { to: "/dashboard", label: "Overview" },
  { to: "/repositories", label: "Repositories" },
  { to: "/connect", label: "GitHub connection" },
];

function ConnectionStatus() {
  const { state } = useConnection();
  if (state.status !== "ready") return null;
  const { connection } = state;

  return (
    <div className="sidebar-status">
      {connection.status === "active" && (
        <>
          <strong>
            <span aria-hidden="true">✓</span> GitHub connected
          </strong>
          <span>
            {connection.repository_count}{" "}
            {connection.repository_count === 1 ? "repository" : "repositories"} available
          </span>
        </>
      )}
      {connection.status === "needs_attention" && (
        <strong>
          <span aria-hidden="true">!</span> GitHub needs attention
        </strong>
      )}
      {connection.status === "not_connected" && <strong>GitHub not connected</strong>}
    </div>
  );
}

// The signed-in layout (design mockup 07).
export default function AppShell() {
  const { state } = useAuth();
  const { pathname } = useLocation();

  return (
    <div className="shell">
      <aside className="sidebar">
        <Link to="/dashboard" className="logo-link" aria-label="DevPulse home">
          <Logo tone="light" />
        </Link>
        {state.status === "authenticated" && (
          <div className="sidebar-workspace">
            <span className="sidebar-eyebrow">Signed in as</span>
            <strong className="mono">@{state.user.login}</strong>
          </div>
        )}
        <nav className="nav" aria-label="Primary">
          {NAV_ITEMS.map((item) => (
            <NavLink key={item.to} to={item.to}>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <ConnectionStatus />
          <LogoutButton className="sidebar-action" />
        </div>
      </aside>
      <main className="main">
        <header className="topbar">
          <span>DevPulse / {PAGE_LABELS[pathname] ?? "Home"}</span>
          <span>Times shown in UTC</span>
        </header>
        <Outlet />
      </main>
    </div>
  );
}
