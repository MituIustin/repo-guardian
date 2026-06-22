import { useEffect, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { getCurrentUser, logout, type CurrentUser } from "./api/auth";
import { AppShell } from "./components/AppShell";
import { BuildsPage } from "./pages/BuildsPage";
import { PlaceholderPage } from "./pages/PlaceholderPage";
import { OverviewPage } from "./pages/OverviewPage";
import { RepositoriesPage } from "./pages/RepositoriesPage";
import { SettingsPage } from "./pages/SettingsPage";

export type AuthState =
  | { status: "loading" }
  | { status: "anonymous" }
  | { status: "authenticated"; user: CurrentUser }
  | { status: "error" };

export default function App() {
  const [auth, setAuth] = useState<AuthState>({ status: "loading" });

  useEffect(() => {
    void getCurrentUser()
      .then((user) =>
        setAuth(
          user ? { status: "authenticated", user } : { status: "anonymous" },
        ),
      )
      .catch(() => setAuth({ status: "error" }));
  }, []);

  const handleLogout = async () => {
    try {
      await logout();
      setAuth({ status: "anonymous" });
    } catch {
      setAuth({ status: "error" });
    }
  };

  return (
    <AppShell auth={auth} onLogout={() => void handleLogout()}>
      <Routes>
        <Route path="/" element={<OverviewPage auth={auth} />} />
        <Route
          path="/repositories"
          element={<RepositoriesPage auth={auth} />}
        />
        <Route path="/builds" element={<BuildsPage auth={auth} />} />
        <Route
          path="/incidents"
          element={
            <PlaceholderPage
              auth={auth}
              title="Incidents"
              description="Failed-build investigations will appear here after incident ingestion is implemented."
            />
          }
        />
        <Route path="/settings" element={<SettingsPage auth={auth} />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  );
}
