export interface GitHubAppInstallation {
  installationId: number;
  accountLogin: string;
  accountType: string;
  repositorySelection: string;
  status: string;
  monitoringEnabled: boolean;
  repositoryCount: number;
  lastSyncedAt: string | null;
}

export interface GitHubAppStatus {
  configured: boolean;
  installed: boolean;
  totalRepositoryCount: number;
  installations: GitHubAppInstallation[];
}

async function request(url: string, init?: RequestInit): Promise<Response> {
  const response = await fetch(url, {
    ...init,
    credentials: "include",
    headers: { Accept: "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as {
      detail?: string;
    } | null;
    throw new Error(
      payload?.detail ??
        `GitHub App request failed with status ${response.status}`,
    );
  }
  return response;
}

export async function getGitHubAppStatus(): Promise<GitHubAppStatus> {
  return (await request("/api/github-app/status")).json() as Promise<GitHubAppStatus>;
}

export async function synchronizeInstallation(
  installationId: number,
): Promise<void> {
  await request(`/api/github-app/installations/${installationId}/synchronize`, {
    method: "POST",
  });
}

export async function disconnectInstallationRepositories(
  installationId: number,
): Promise<void> {
  await request(`/api/github-app/installations/${installationId}/repositories`, {
    method: "DELETE",
  });
}

export async function uninstallInstallation(
  installationId: number,
): Promise<void> {
  await request(`/api/github-app/installations/${installationId}`, {
    method: "DELETE",
  });
}
