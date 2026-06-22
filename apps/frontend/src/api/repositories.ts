export interface AvailableRepository {
  githubRepositoryId: number;
  name: string;
  fullName: string;
  private: boolean;
  visibility: string;
  htmlUrl: string;
  defaultBranch: string;
  updatedAt: string;
  isConnected: boolean;
}

export interface ConnectedRepository {
  id: string;
  githubRepositoryId: number;
  name: string;
  fullName: string;
  visibility: string;
  htmlUrl: string;
  defaultBranch: string;
  monitoredBranch: string;
  isActive: boolean;
  webhookStatus: "not_configured" | "configured" | "active";
  webhookLastReceivedAt: string | null;
  connectedAt: string;
  installationId: number | null;
  installationAccountLogin: string | null;
  installationAccountType: string | null;
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...init,
    credentials: "include",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as {
      detail?: string;
    } | null;
    throw new Error(
      payload?.detail ?? `Request failed with status ${response.status}`,
    );
  }
  return (response.status === 204 ? undefined : await response.json()) as T;
}

export const getConnectedRepositories = async () =>
  (await request<{ data: ConnectedRepository[] }>("/api/repositories")).data;
export const getAvailableRepositories = async (installationId?: number) =>
  (
    await request<{ data: AvailableRepository[] }>(
      `/api/repositories/available${installationId ? `?installation_id=${installationId}` : ""}`,
    )
  ).data;
export const getRepositoryBranches = async (id: number, installationId?: number) =>
  (
    await request<{ data: { name: string }[] }>(
      `/api/repositories/available/${id}/branches${installationId ? `?installation_id=${installationId}` : ""}`,
    )
  ).data;
export const connectRepository = (
  githubRepositoryId: number,
  monitoredBranch: string,
  installationId?: number,
) =>
  request<ConnectedRepository>("/api/repositories/connect", {
    method: "POST",
    body: JSON.stringify({
      githubRepositoryId,
      monitoredBranch,
      installationId,
    }),
  });
export const updateRepository = (id: string, monitoredBranch: string) =>
  request<ConnectedRepository>(`/api/repositories/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ monitoredBranch }),
  });
export const disconnectRepository = (id: string) =>
  request<void>(`/api/repositories/${id}`, { method: "DELETE" });

export const disconnectAllRepositories = () =>
  request<{ status: string; disconnectedCount: number }>("/api/repositories", {
    method: "DELETE",
  });

export type RepositoryStreamStatus = "connecting" | "live" | "disconnected";

export function connectRepositoryStream(
  onChange: () => void,
  onStatus: (status: RepositoryStreamStatus) => void,
): () => void {
  if (typeof WebSocket === "undefined") {
    onStatus("disconnected");
    return () => undefined;
  }
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const socket = new WebSocket(
    `${protocol}//${window.location.host}/api/repositories/stream`,
  );
  onStatus("connecting");
  socket.addEventListener("open", () => onStatus("live"));
  socket.addEventListener("message", (event) => {
    const message = JSON.parse(event.data) as { type: string };
    if (message.type === "repositories.changed") onChange();
  });
  socket.addEventListener("close", () => onStatus("disconnected"));
  const heartbeat = window.setInterval(() => {
    if (socket.readyState === WebSocket.OPEN) socket.send("ping");
  }, 25000);
  return () => {
    window.clearInterval(heartbeat);
    socket.close();
  };
}
