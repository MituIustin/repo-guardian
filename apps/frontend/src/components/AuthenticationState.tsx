import type { AuthState } from "../App";

export function AuthenticationState({ auth }: { auth: AuthState }) {
  if (auth.status === "loading") {
    return (
      <div className="state-panel" role="status">
        <h2>Checking your session</h2>
        <p>Loading your Repo Guardian workspace.</p>
      </div>
    );
  }
  if (auth.status === "error") {
    return (
      <div className="state-panel state-panel--error" role="alert">
        <h2>Authentication is unavailable</h2>
        <p>
          The API could not confirm your session. Check the local services and
          try again.
        </p>
      </div>
    );
  }
  return (
    <div className="state-panel">
      <span className="state-panel__label">GitHub account required</span>
      <h2>Sign in to use this workspace</h2>
      <p>
        Connect GitHub to view and manage repositories. Repo Guardian does not
        display fabricated account data while you are signed out.
      </p>
      <a className="primary-button" href="/api/auth/github/login">
        Continue with GitHub
      </a>
    </div>
  );
}
