import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import Logo from "./Logo";

type Props = {
  crumb: string;
  action: ReactNode;
  children: ReactNode;
};

// Full-page layout for sign-in and setup steps (design mockup 03).
export default function SetupLayout({ crumb, action, children }: Props) {
  return (
    <div className="setup">
      <header className="setup-header">
        <Link to="/" className="logo-link" aria-label="DevPulse home">
          <Logo />
        </Link>
        <span className="setup-crumb">{crumb}</span>
        {action}
      </header>
      <main className="setup-body">{children}</main>
    </div>
  );
}
