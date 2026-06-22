export interface CurrentUser {
  id: string;
  name: string;
  email: string | null;
  avatarUrl: string | null;
  githubUsername: string;
}

export async function getCurrentUser(): Promise<CurrentUser | null> {
  const response = await fetch("/api/auth/me", {
    credentials: "include",
    headers: { Accept: "application/json" },
  });

  if (response.status === 401) {
    return null;
  }
  if (!response.ok) {
    throw new Error(
      `Current user request failed with status ${response.status}`,
    );
  }
  return (await response.json()) as CurrentUser;
}

export async function logout(): Promise<void> {
  const response = await fetch("/api/auth/logout", {
    method: "POST",
    credentials: "include",
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    throw new Error(`Logout request failed with status ${response.status}`);
  }
}
