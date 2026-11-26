import { Link } from "react-router-dom";

export function ConnectPrompt() {
  return (
    <section className="card prompt" aria-labelledby="prompt-title">
      <h2 id="prompt-title">Connect GitHub to see your pull requests.</h2>
      <p>
        DevPulse reads your pull request activity from the repositories you choose, with read-only
        access. Your source code stays on GitHub.
      </p>
      <Link className="btn btn-primary" to="/connect">
        Connect GitHub <span aria-hidden="true">→</span>
      </Link>
    </section>
  );
}

export function SelectRepositoriesPrompt() {
  return (
    <section className="card prompt" aria-labelledby="prompt-title">
      <h2 id="prompt-title">Choose the repositories to track.</h2>
      <p>
        No repositories are selected yet. Pick the ones that matter now, and DevPulse will start
        importing their pull requests.
      </p>
      <Link className="btn btn-primary" to="/repositories">
        Select repositories <span aria-hidden="true">→</span>
      </Link>
    </section>
  );
}
