import Landing from "./Landing";
import "./styles/landing.css";

export default function App() {
  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="logo">DevPulse</div>
        <nav className="nav" aria-label="Primary">
          <a href="#overview" aria-current="page">
            Overview
          </a>
          <a href="#cicd">CI/CD insights</a>
          <a href="#technology">Technology insights</a>
        </nav>
      </aside>
      <main className="main">
        <Landing />
      </main>
    </div>
  );
}
