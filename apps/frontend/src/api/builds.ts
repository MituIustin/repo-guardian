export interface BuildJob {
  id: string;
  name: string;
  status: string;
  conclusion: string | null;
  htmlUrl: string;
  startedAt: string | null;
  completedAt: string | null;
  steps: BuildStep[];
}

export interface BuildStep {
  name: string;
  status: string;
  conclusion: string | null;
  number: number;
  startedAt: string | null;
  completedAt: string | null;
}

export interface LogExcerpt {
  sourceFile: string | null;
  startLine: number;
  endLine: number;
  content: string;
}

export interface Build {
  id: string;
  repositoryId: string;
  repositoryFullName: string;
  githubRunId: number;
  workflowName: string;
  runNumber: number;
  runAttempt: number;
  branch: string;
  commitSha: string;
  status: string;
  conclusion: string | null;
  event: string;
  htmlUrl: string;
  startedAt: string | null;
  completedAt: string | null;
  updatedAt: string;
  jobs: BuildJob[];
  errorExcerpt: LogExcerpt | null;
}

export async function getBuilds(): Promise<Build[]> {
  const response = await fetch("/api/builds", {
    credentials: "include",
    headers: { Accept: "application/json" },
  });
  if (!response.ok)
    throw new Error(`Build request failed with status ${response.status}`);
  return ((await response.json()) as { data: Build[] }).data;
}

async function rerunRequest(url: string, body?: object): Promise<void> {
  const response = await fetch(url, {
    method: "POST",
    credentials: "include",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as {
      detail?: string;
    } | null;
    throw new Error(
      payload?.detail ?? `Rerun request failed with status ${response.status}`,
    );
  }
}

export const rerunWorkflow = (buildId: string, mode: "all" | "failed") =>
  rerunRequest(`/api/builds/${buildId}/rerun`, { mode });

export const rerunJob = (jobId: string) =>
  rerunRequest(`/api/builds/jobs/${jobId}/rerun`);

export type BuildStreamStatus = "connecting" | "live" | "disconnected";

export function connectBuildStream(
  onBuild: (build: Build) => void,
  onStatus: (status: BuildStreamStatus) => void,
): () => void {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const socket = new WebSocket(
    `${protocol}//${window.location.host}/api/builds/stream`,
  );
  onStatus("connecting");
  socket.addEventListener("open", () => onStatus("live"));
  socket.addEventListener("message", (event) => {
    const message = JSON.parse(event.data) as { type: string; data?: Build };
    if (message.type === "workflow_run.updated" && message.data)
      onBuild(message.data);
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
