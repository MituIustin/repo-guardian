import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";
import type { AuthState } from "../App";

const navigation = [
  { label: "Overview", path: "/", end: true },
  { label: "Repositories", path: "/repositories" },
  { label: "Builds", path: "/builds" },
  { label: "Incidents", path: "/incidents" },
  { label: "Settings", path: "/settings" },
];

interface AppShellProps {
  auth: AuthState;
  children: ReactNode;
  onLogout: () => void;
}

export function AppShell({ auth, children, onLogout }: AppShellProps) {
  return (
    <div className="dashboard-shell">
      <aside className="sidebar">
        <NavLink className="brand" to="/" aria-label="Repo Guardian dashboard">
          <span className="brand__mark">RG</span>
          <span>Repo Guardian</span>
        </NavLink>
        <nav className="primary-nav" aria-label="Primary navigation">
          {navigation.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.end}
              className={({ isActive }) =>
                `nav-link${isActive ? " nav-link--active" : ""}`
              }
            >
              <span className="nav-link__indicator" aria-hidden="true" />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar__footer">
          <span className="environment-dot" aria-hidden="true" />
          Local development
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <span className="topbar__context">CI/CD monitoring workspace</span>
          {auth.status === "authenticated" ? (
            <div className="account-menu">
              {auth.user.avatarUrl ? (
                <img src={auth.user.avatarUrl} alt="" />
              ) : (
                <span className="avatar-fallback">
                  {auth.user.githubUsername.slice(0, 1).toUpperCase()}
                </span>
              )}
              <div>
                <strong>{auth.user.name}</strong>
                <small>@{auth.user.githubUsername}</small>
              </div>
              <button className="text-button" type="button" onClick={onLogout}>
                Sign out
              </button>
            </div>
          ) : (
            <a
              className="primary-button primary-button--compact"
              href="/api/auth/github/login"
            >
              Sign in with GitHub
            </a>
          )}
        </header>
        <main className="page-content">{children}</main>
      </div>
    </div>
  );
}
