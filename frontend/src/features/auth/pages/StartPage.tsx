import { useAuth } from "../hooks/useAuth";

// Temporary landing spot after sign-in. The connect-GitHub page replaces it in the next slice.
export default function StartPage() {
  const { state } = useAuth();
  if (state.status !== "authenticated") return null;
  const { user } = state;

  return (
    <div className="content">
      <h1 className="page-title">You are signed in</h1>
      <div className="card">
        <h2>Welcome, {user.name ?? user.login}</h2>
        <p>
          Signed in as <span className="mono">@{user.login}</span>. Connecting your GitHub account
          comes next.
        </p>
      </div>
    </div>
  );
}
