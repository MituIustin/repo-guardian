import type { AuthState } from "../App";
import { AuthenticationState } from "../components/AuthenticationState";

export function OverviewPage({ auth }: { auth: AuthState }) {
  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Workspace</p>
          <h1>Overview</h1>
          <p>
            Monitor repository connections and prepare for CI/CD incident
            investigation.
          </p>
        </div>
      </div>
      {auth.status !== "authenticated" ? (
        <AuthenticationState auth={auth} />
      ) : (
        <div className="content-panel">
          <span className="status-badge status-badge--connected">
            GitHub connected
          </span>
          <h2>Welcome, {auth.user.name}</h2>
          <p>
            Connect a repository to establish the first monitored project. Build
            and incident information will remain empty until webhook processing
            is implemented.
          </p>
          <a className="primary-button" href="/repositories">
            Manage repositories
          </a>
        </div>
      )}
    </>
  );
}
