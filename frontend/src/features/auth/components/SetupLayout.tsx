import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import Logo from "../../../shared/components/Logo";

// Full-page layout for sign-in and setup steps (design mockup 03).
export default function SetupLayout({ children }: { children: ReactNode }) {
  return (
    <div className="setup">
      <header className="setup-header">
        <Link to="/" className="logo-link" aria-label="DevPulse home">
          <Logo />
        </Link>
        <span className="setup-crumb">Sign in</span>
        <Link to="/" className="btn btn-ghost">
          Back to home
        </Link>
      </header>
      <main className="setup-body">{children}</main>
    </div>
  );
}
