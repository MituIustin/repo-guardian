import { useEffect, useMemo, useState } from "react";
import type { AuthState } from "../App";
import {
  connectBuildStream,
  getBuilds,
  rerunJob,
  rerunWorkflow,
  type Build,
  type BuildStreamStatus,
} from "../api/builds";
import { AuthenticationState } from "../components/AuthenticationState";

type BuildFilter = "all" | "running" | "failed" | "passed" | "other";

function buildState(build: Build): Exclude<BuildFilter, "all"> {
  if (build.status !== "completed") return "running";
  if (build.conclusion === "success") return "passed";
  if (
    ["failure", "timed_out", "action_required", "startup_failure"].includes(
      build.conclusion ?? "",
    )
  )
    return "failed";
  return "other";
}

function stateLabel(build: Build): string {
  const state = buildState(build);
  if (state === "running")
    return build.status === "queued" ? "Queued" : "In progress";
  if (state === "passed") return "Succeeded";
  if (state === "failed") return "Failed";
  return build.conclusion ?? build.status;
}

function repositoryParts(fullName: string): { owner: string; name: string } {
  const [owner, ...name] = fullName.split("/");
  return { owner, name: name.join("/") };
}

function duration(startedAt: string | null, completedAt: string | null): string {
  if (!startedAt) return "Not started";
  const end = completedAt ? Date.parse(completedAt) : Date.now();
  const seconds = Math.max(0, Math.round((end - Date.parse(startedAt)) / 1000));
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  return `${minutes}m ${seconds % 60}s`;
}

export function BuildsPage({ auth }: { auth: AuthState }) {
  const [builds, setBuilds] = useState<Build[]>([]);
  const [filter, setFilter] = useState<BuildFilter>("all");
  const [repository, setRepository] = useState("all");
  const [query, setQuery] = useState("");
  const [stream, setStream] = useState<BuildStreamStatus>("connecting");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [rerunning, setRerunning] = useState<string | null>(null);
  const [expandedBuilds, setExpandedBuilds] = useState<Set<string>>(new Set());
  const [expandedRepositories, setExpandedRepositories] = useState<Set<string>>(
    new Set(),
  );

  useEffect(() => {
    if (auth.status !== "authenticated") return;
    void getBuilds()
      .then(setBuilds)
      .catch(() => setError("Build activity could not be loaded."))
      .finally(() => setLoading(false));
    return connectBuildStream(
      (updated) =>
        setBuilds((current) =>
          [updated, ...current.filter((item) => item.id !== updated.id)].sort(
            (left, right) =>
              Date.parse(right.updatedAt) - Date.parse(left.updatedAt),
          ),
        ),
      setStream,
    );
  }, [auth.status]);

  const repositoryNames = useMemo(
    () => [...new Set(builds.map((build) => build.repositoryFullName))].sort(),
    [builds],
  );

  const latestByRepository = useMemo(() => {
    const latest = new Map<string, Build>();
    for (const build of builds) {
      if (!latest.has(build.repositoryFullName))
        latest.set(build.repositoryFullName, build);
    }
    return [...latest.values()];
  }, [builds]);

  const groupedBuilds = useMemo(() => {
    const term = query.trim().toLowerCase();
    const filtered = builds.filter((build) => {
      const matchesRepository =
        repository === "all" || build.repositoryFullName === repository;
      const matchesState = filter === "all" || buildState(build) === filter;
      const matchesQuery =
        !term ||
        build.repositoryFullName.toLowerCase().includes(term) ||
        build.workflowName.toLowerCase().includes(term) ||
        build.branch.toLowerCase().includes(term) ||
        build.commitSha.toLowerCase().startsWith(term);
      return matchesRepository && matchesState && matchesQuery;
    });
    const groups = new Map<string, Build[]>();
    for (const build of filtered) {
      const current = groups.get(build.repositoryFullName) ?? [];
      current.push(build);
      groups.set(build.repositoryFullName, current);
    }
    return [...groups.entries()].sort(([left], [right]) =>
      left.localeCompare(right),
    );
  }, [builds, filter, query, repository]);

  const counts = useMemo(
    () => ({
      repositories: latestByRepository.length,
      running: latestByRepository.filter((build) => buildState(build) === "running")
        .length,
      failed: latestByRepository.filter((build) => buildState(build) === "failed")
        .length,
      passed: latestByRepository.filter((build) => buildState(build) === "passed")
        .length,
    }),
    [latestByRepository],
  );

  const toggleBuild = (buildId: string) => {
    setExpandedBuilds((current) => {
      const next = new Set(current);
      if (next.has(buildId)) next.delete(buildId);
      else next.add(buildId);
      return next;
    });
  };

  const toggleRepository = (fullName: string) => {
    setExpandedRepositories((current) => {
      const next = new Set(current);
      if (next.has(fullName)) next.delete(fullName);
      else next.add(fullName);
      return next;
    });
  };

  const requestWorkflowRerun = async (
    build: Build,
    mode: "all" | "failed",
  ) => {
    const label = mode === "failed" ? "failed jobs" : "the complete workflow";
    if (!window.confirm(`Rerun ${label} for ${build.workflowName}?`)) return;
    setRerunning(`${build.id}-${mode}`);
    setError(null);
    setNotice(null);
    try {
      await rerunWorkflow(build.id, mode);
      setNotice(
        `GitHub accepted the rerun request for ${build.repositoryFullName}.`,
      );
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "The workflow could not be rerun.",
      );
    } finally {
      setRerunning(null);
    }
  };

  const requestJobRerun = async (jobId: string, jobName: string) => {
    if (!window.confirm(`Rerun the ${jobName} job?`)) return;
    setRerunning(jobId);
    setError(null);
    setNotice(null);
    try {
      await rerunJob(jobId);
      setNotice(`GitHub accepted the rerun request for ${jobName}.`);
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "The job could not be rerun.",
      );
    } finally {
      setRerunning(null);
    }
  };

  const renderBuild = (build: Build, latest: boolean) => {
    const state = buildState(build);
    const expanded = expandedBuilds.has(build.id);
    return (
      <article
        className={`build-run ${expanded ? "build-run--expanded" : ""}`}
        key={build.id}
      >
        <button
          className="build-run__summary"
          type="button"
          aria-expanded={expanded}
          onClick={() => toggleBuild(build.id)}
        >
          <span className={`build-status build-status--${state}`}>
            {stateLabel(build)}
          </span>
          <span className="build-run__workflow">
            <strong>{build.workflowName}</strong>
            <small>
              Run #{build.runNumber} · attempt {build.runAttempt}
              {latest ? " · latest" : ""}
            </small>
          </span>
          <span className="build-run__branch">
            <small>Branch</small>
            <strong>{build.branch}</strong>
          </span>
          <span className="build-run__time">
            <small>{duration(build.startedAt, build.completedAt)}</small>
            <strong>{new Date(build.updatedAt).toLocaleString()}</strong>
          </span>
          <span className="build-run__expand">{expanded ? "Hide" : "Details"}</span>
        </button>

        {expanded ? (
          <div className="build-run__details">
            <div className="build-detail-actions">
              <div>
                <span>Commit</span>
                <code>{build.commitSha.slice(0, 12)}</code>
                <span>Triggered by {build.event}</span>
              </div>
              <div>
                {state === "failed" ? (
                  <button
                    className="primary-button"
                    type="button"
                    disabled={rerunning !== null}
                    onClick={() => void requestWorkflowRerun(build, "failed")}
                  >
                    {rerunning === `${build.id}-failed`
                      ? "Requesting..."
                      : "Rerun failed jobs"}
                  </button>
                ) : null}
                {build.status === "completed" ? (
                  <button
                    className="secondary-button"
                    type="button"
                    disabled={rerunning !== null}
                    onClick={() => void requestWorkflowRerun(build, "all")}
                  >
                    {rerunning === `${build.id}-all`
                      ? "Requesting..."
                      : "Rerun workflow"}
                  </button>
                ) : null}
                <a
                  className="secondary-button"
                  href={build.htmlUrl}
                  target="_blank"
                  rel="noreferrer"
                >
                  Open in GitHub
                </a>
              </div>
            </div>

            <section className="build-jobs" aria-label="Jobs and steps">
              <h4>Jobs and steps</h4>
              {build.jobs.length === 0 ? (
                <p className="build-note">Job details are not available yet.</p>
              ) : (
                build.jobs.map((job) => (
                  <div className="build-job" key={job.id}>
                    <div className="build-job__header">
                      <a href={job.htmlUrl} target="_blank" rel="noreferrer">
                        {job.name}
                      </a>
                      <span>{job.conclusion ?? job.status}</span>
                      {job.status === "completed" ? (
                        <button
                          className="text-button"
                          type="button"
                          disabled={rerunning !== null}
                          onClick={() => void requestJobRerun(job.id, job.name)}
                        >
                          {rerunning === job.id ? "Requesting..." : "Rerun job"}
                        </button>
                      ) : null}
                    </div>
                    {job.steps.length > 0 ? (
                      <ol className="build-steps">
                        {job.steps.map((step) => (
                          <li key={`${step.number}-${step.name}`}>
                            <span
                              className={`step-state step-state--${step.conclusion ?? step.status}`}
                              aria-hidden="true"
                            />
                            <strong>{step.name}</strong>
                            <small>{step.conclusion ?? step.status}</small>
                          </li>
                        ))}
                      </ol>
                    ) : (
                      <p className="build-note">Step details were not supplied by GitHub.</p>
                    )}
                  </div>
                ))
              )}
            </section>

            {build.errorExcerpt ? (
              <details className="error-evidence" open>
                <summary>Extracted failure evidence</summary>
                <p>
                  {build.errorExcerpt.sourceFile ?? "Workflow log"}, lines{" "}
                  {build.errorExcerpt.startLine}-{build.errorExcerpt.endLine}
                </p>
                <pre>{build.errorExcerpt.content}</pre>
              </details>
            ) : state === "failed" ? (
              <p className="build-note">
                The failure was recorded, but no recognizable error excerpt was found.
              </p>
            ) : null}
          </div>
        ) : null}
      </article>
    );
  };

  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">CI monitoring</p>
          <h1>Builds</h1>
          <p>
            Latest repository health first, with workflow history, jobs, steps,
            failure evidence, and controlled rerun actions.
          </p>
        </div>
        {auth.status === "authenticated" ? (
          <span className={`live-status live-status--${stream}`}>
            <span aria-hidden="true" />
            {stream === "live"
              ? "Live updates connected"
              : stream === "connecting"
                ? "Connecting live updates"
                : "Live updates disconnected"}
          </span>
        ) : null}
      </div>

      {auth.status !== "authenticated" ? (
        <AuthenticationState auth={auth} />
      ) : (
        <>
          {error ? <div className="inline-alert" role="alert">{error}</div> : null}
          {notice ? <div className="inline-notice" role="status">{notice}</div> : null}

          <div className="build-overview" aria-label="Latest build summary">
            <div><span>Repositories</span><strong>{counts.repositories}</strong></div>
            <div><span>Running</span><strong>{counts.running}</strong></div>
            <div><span>Failed</span><strong>{counts.failed}</strong></div>
            <div><span>Passing</span><strong>{counts.passed}</strong></div>
          </div>

          <div className="build-controls">
            <label className="build-search">
              <span>Search</span>
              <input
                type="search"
                value={query}
                placeholder="Repository, workflow, branch, or commit"
                onChange={(event) => setQuery(event.target.value)}
              />
            </label>
            <label>
              <span>Repository</span>
              <select value={repository} onChange={(event) => setRepository(event.target.value)}>
                <option value="all">All repositories</option>
                {repositoryNames.map((name) => <option key={name} value={name}>{name}</option>)}
              </select>
            </label>
            <label>
              <span>Status</span>
              <select value={filter} onChange={(event) => setFilter(event.target.value as BuildFilter)}>
                <option value="all">All statuses</option>
                <option value="running">Running</option>
                <option value="failed">Failed</option>
                <option value="passed">Passed</option>
                <option value="other">Other</option>
              </select>
            </label>
          </div>

          {loading ? (
            <div className="empty-state content-panel"><h2>Loading build activity</h2></div>
          ) : groupedBuilds.length === 0 ? (
            <div className="empty-state content-panel">
              <span>No workflow runs</span>
              <h2>No builds match the current view</h2>
              <p>Clear the filters or wait for GitHub Actions activity.</p>
            </div>
          ) : (
            <div className="repository-builds">
              {groupedBuilds.map(([fullName, repositoryBuilds]) => {
                const { owner, name } = repositoryParts(fullName);
                const historyExpanded = expandedRepositories.has(fullName);
                const visible = historyExpanded
                  ? repositoryBuilds
                  : repositoryBuilds.slice(0, 1);
                return (
                  <section className="repository-build-group" key={fullName}>
                    <header className="repository-build-group__header">
                      <div className="repository-identity">
                        <span aria-hidden="true">{owner.slice(0, 1).toUpperCase()}</span>
                        <div>
                          <small>{owner}</small>
                          <h2>{name}</h2>
                        </div>
                      </div>
                      <div className="repository-build-group__actions">
                        <a href={`https://github.com/${fullName}`} target="_blank" rel="noreferrer">
                          Open repository
                        </a>
                        {repositoryBuilds.length > 1 ? (
                          <button className="text-button" type="button" onClick={() => toggleRepository(fullName)}>
                            {historyExpanded
                              ? "Show latest only"
                              : `Show ${repositoryBuilds.length - 1} previous runs`}
                          </button>
                        ) : null}
                      </div>
                    </header>
                    <div className="repository-build-group__runs">
                      {visible.map((build, index) => renderBuild(build, index === 0))}
                    </div>
                  </section>
                );
              })}
            </div>
          )}
        </>
      )}
    </>
  );
}
