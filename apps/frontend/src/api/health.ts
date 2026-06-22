export interface HealthResponse {
  status: "ok";
  service: string;
  version: string;
}

export interface ReadinessResponse {
  status: "ready" | "not_ready";
  service: string;
  version: string;
  checks: {
    database: "ok" | "unavailable";
  };
}

export interface ServiceHealth {
  api: HealthResponse;
  readiness: ReadinessResponse;
}

async function readJson<T>(url: string, allowUnavailable = false): Promise<T> {
  const response = await fetch(url, {
    headers: { Accept: "application/json" },
  });

  if (!response.ok && !(allowUnavailable && response.status === 503)) {
    throw new Error(`Health request failed with status ${response.status}`);
  }

  return (await response.json()) as T;
}

export async function getServiceHealth(): Promise<ServiceHealth> {
  const [api, readiness] = await Promise.all([
    readJson<HealthResponse>("/api/health"),
    readJson<ReadinessResponse>("/api/ready", true),
  ]);

  return { api, readiness };
}
