import type { AuthState } from "../App";
import { AuthenticationState } from "../components/AuthenticationState";

export function SettingsPage({ auth }: { auth: AuthState }) {
  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Workspace</p>
          <h1>Settings</h1>
          <p>Review the identity connected to Repo Guardian.</p>
        </div>
      </div>
      {auth.status !== "authenticated" ? (
        <AuthenticationState auth={auth} />
      ) : (
        <div className="content-panel">
          <h2>GitHub identity</h2>
          <dl className="detail-list">
            <div>
              <dt>Account</dt>
              <dd>@{auth.user.githubUsername}</dd>
            </div>
            <div>
              <dt>Email</dt>
              <dd>{auth.user.email ?? "Not provided by GitHub"}</dd>
            </div>
            <div>
              <dt>Connection</dt>
              <dd>Active</dd>
            </div>
          </dl>
        </div>
      )}
    </>
  );
}
