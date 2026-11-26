import { Link } from "react-router-dom";

const DEPLOY_BARS = [28, 40, 34, 52, 46, 62, 58, 48, 70, 60, 76, 66, 84, 78, 92, 86];

const AUDIENCES = ["Engineering leads", "Platform teams", "Growing organisations"];

const FEATURES = [
  {
    n: "01",
    title: "See the work move",
    body: "Track deployment frequency and pull request cycle time across your repositories.",
    link: "Overview dashboard",
  },
  {
    n: "02",
    title: "Make delivery reliable",
    body: "Spot failed workflows, understand the cause and get straight to the run that matters.",
    link: "CI/CD insights",
  },
  {
    n: "03",
    title: "Know your stack",
    body: "See where languages and frameworks live, and which repositories depend on them.",
    link: "Technology insights",
  },
];

const STEPS = [
  {
    n: "01",
    title: "Connect securely",
    body: "Install the GitHub App with fine-grained, read-only permissions.",
  },
  {
    n: "02",
    title: "Choose your repositories",
    body: "Start with your active projects. Keep control over what is included.",
  },
  {
    n: "03",
    title: "Find your next move",
    body: "Import your full pull request history, then stay current with updates every 15 minutes.",
  },
];

const GUARANTEES = [
  "Read-only GitHub App permissions",
  "Repository-level access controls",
  "No write access to code or workflows",
  "Revoke access whenever you need",
];

const FAQ = [
  {
    q: "Does DevPulse change my repositories?",
    a: "No. DevPulse is read-only. Code changes, re-runs and deployments stay in GitHub.",
  },
  {
    q: "How far back does the first sync go?",
    a: "Your first sync imports the full pull request history of the repositories you select. Very large histories can take several update cycles to finish.",
  },
  {
    q: "Can I start with just a few repositories?",
    a: "Yes. Choose the repositories that matter now and update your selection as your team grows.",
  },
];

function ConnectButton() {
  return (
    <Link to="/sign-in" className="lp-btn lp-btn-primary">
      Continue with GitHub →
    </Link>
  );
}

export default function Landing() {
  return (
    <div className="lp">
      <header className="lp-nav">
        <nav className="lp-nav-links" aria-label="Landing">
          <a href="#platform">Platform</a>
          <a href="#how-it-works">How it works</a>
          <a href="#security">Security</a>
        </nav>
        <ConnectButton />
      </header>

      <section className="lp-hero">
        <div className="lp-hero-copy">
          <p className="lp-eyebrow">Less guesswork. More momentum.</p>
          <h1 className="lp-hero-title">
            The full picture.
            <br />
            From commit
            <br />
            to production.
          </h1>
          <p className="lp-lead">
            Bring GitHub activity, CI/CD health and your technology stack into one clear view.
            Know what’s moving. Find what needs you.
          </p>
          <div className="lp-actions">
            <ConnectButton />
            <button type="button" className="lp-btn lp-btn-secondary">
              Explore the demo
            </button>
          </div>
          <p className="lp-fine">Read-only access · Choose your repositories · Set up in minutes</p>
        </div>

        <aside className="lp-preview" aria-label="Example dashboard preview">
          <div className="lp-preview-head">
            <span>devpulse / acme-engineering</span>
            <span className="lp-live">● Live</span>
          </div>
          <h2 className="lp-preview-title">Delivery, without the blind spots.</h2>
          <div className="lp-preview-stats">
            <div className="lp-stat">
              <strong>12.4</strong>
              <span>deploys / day</span>
            </div>
            <div className="lp-stat">
              <strong>94.8%</strong>
              <span>workflow success</span>
            </div>
            <div className="lp-stat">
              <strong>18.6h</strong>
              <span>cycle time</span>
            </div>
          </div>
          <div className="lp-chart">
            <span className="lp-chart-title">Deployment activity</span>
            <div className="lp-bars" aria-hidden="true">
              {DEPLOY_BARS.map((h, i) => (
                <span key={i} style={{ height: `${h}%` }} />
              ))}
            </div>
          </div>
          <p className="lp-preview-foot">↑ 18.2% more deployments this month</p>
        </aside>
      </section>

      <section className="lp-audience" aria-label="Who it is for">
        <span className="lp-audience-label">Built for the people behind the release</span>
        {AUDIENCES.map((a) => (
          <span key={a}>{a}</span>
        ))}
      </section>

      <section className="lp-section" id="platform">
        <h2 className="lp-h2">Every signal. One shared understanding.</h2>
        <p className="lp-sub">Move from scattered tabs to a connected engineering story.</p>
        <div className="lp-cards">
          {FEATURES.map((f) => (
            <article key={f.n} className="lp-card">
              <span className="lp-card-n">{f.n}</span>
              <h3>{f.title}</h3>
              <p>{f.body}</p>
              <a href="#platform">{f.link} →</a>
            </article>
          ))}
        </div>
      </section>

      <section className="lp-steps" id="how-it-works">
        <h2 className="lp-h2">From connection to clarity in minutes.</h2>
        <div className="lp-steps-grid">
          {STEPS.map((s) => (
            <div key={s.n}>
              <span className="lp-step-n">{s.n}</span>
              <h3>{s.title}</h3>
              <p>{s.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="lp-security" id="security">
        <div>
          <h2 className="lp-h2">Your source stays yours.</h2>
          <p className="lp-sub">
            Useful insight shouldn’t come at the cost of control. DevPulse reads activity and
            workflow metadata—not your secrets.
          </p>
        </div>
        <ul className="lp-checks">
          {GUARANTEES.map((g) => (
            <li key={g}>
              <span aria-hidden="true">✓</span> {g}
            </li>
          ))}
        </ul>
      </section>

      <section className="lp-section">
        <h2 className="lp-h2">A few things worth knowing.</h2>
        <div className="lp-faq">
          {FAQ.map((f) => (
            <div key={f.q} className="lp-faq-item">
              <h3>{f.q}</h3>
              <p>{f.a}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="lp-cta">
        <h2 className="lp-h2">Your team’s next chapter, in focus.</h2>
        <p className="lp-sub">Start with GitHub. Leave with a clearer direction.</p>
        <ConnectButton />
      </section>

      <footer className="lp-footer">
        <span>
          <strong>devpulse</strong> / Engineering intelligence
        </span>
        <span className="lp-footer-links">
          <a href="#privacy">Privacy</a>
          <a href="#terms">Terms</a>
          <a href="#contact">Contact</a>
          <span>© 2026 DevPulse</span>
        </span>
      </footer>
    </div>
  );
}
