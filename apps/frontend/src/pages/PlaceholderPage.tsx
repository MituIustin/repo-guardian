import type { AuthState } from "../App";
import { AuthenticationState } from "../components/AuthenticationState";

export function PlaceholderPage({
  auth,
  title,
  description,
}: {
  auth: AuthState;
  title: string;
  description: string;
}) {
  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Dashboard</p>
          <h1>{title}</h1>
          <p>{description}</p>
        </div>
      </div>
      {auth.status !== "authenticated" ? (
        <AuthenticationState auth={auth} />
      ) : (
        <div className="empty-state">
          <span>Not available yet</span>
          <h2>No {title.toLowerCase()} to display</h2>
          <p>{description}</p>
        </div>
      )}
    </>
  );
}
