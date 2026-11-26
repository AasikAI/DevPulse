import { useAuth } from "../hooks/useAuth";

// Temporary landing spot after sign-in. The connect-GitHub page replaces it in the next slice.
export default function StartPage() {
  const { state } = useAuth();
  if (state.status !== "authenticated") return null;
  const { user } = state;

  return (
    <main className="content">
      <header>
        <h1 className="page-title">You are signed in</h1>
        <p className="page-subtitle">Your DevPulse account is ready.</p>
      </header>
      <p className="banner banner-success">
        <strong>
          <span aria-hidden="true">✓</span> Signed in.
        </strong>
        Next, connect your GitHub account to bring in your pull request data.
      </p>
      <div className="card">
        <h2>Welcome, {user.name ?? user.login}</h2>
        <p>
          Signed in as <span className="mono">@{user.login}</span>. Connecting your GitHub account
          comes next.
        </p>
      </div>
    </main>
  );
}
