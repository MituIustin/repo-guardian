import { useCallback, useEffect, useMemo, useState } from "react";
import type { AuthState } from "../App";
import {
  disconnectInstallationRepositories,
  getGitHubAppStatus,
  synchronizeInstallation,
  uninstallInstallation,
  type GitHubAppStatus,
} from "../api/githubApp";
import {
  connectRepository,
  connectRepositoryStream,
  disconnectAllRepositories,
  disconnectRepository,
  getAvailableRepositories,
  getConnectedRepositories,
  getRepositoryBranches,
  updateRepository,
  type AvailableRepository,
  type ConnectedRepository,
  type RepositoryStreamStatus,
} from "../api/repositories";
import { AuthenticationState } from "../components/AuthenticationState";

export function RepositoriesPage({ auth }: { auth: AuthState }) {
  const [connected, setConnected] = useState<ConnectedRepository[]>([]);
  const [githubApp, setGitHubApp] = useState<GitHubAppStatus | null>(null);
  const [available, setAvailable] = useState<AvailableRepository[]>([]);
  const [branches, setBranches] = useState<string[]>([]);
  const [connectionBranches, setConnectionBranches] = useState<
    Record<string, string[]>
  >({});
  const [selected, setSelected] = useState<AvailableRepository | null>(null);
  const [selectedSource, setSelectedSource] = useState("");
  const [branch, setBranch] = useState("");
  const [search, setSearch] = useState("");
  const [adding, setAdding] = useState(false);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [stream, setStream] =
    useState<RepositoryStreamStatus>("connecting");

  const loadWorkspace = useCallback(async (showLoading = true) => {
    if (showLoading) setLoading(true);
    try {
      const [repositories, status] = await Promise.all([
        getConnectedRepositories(),
        getGitHubAppStatus(),
      ]);
      setConnected(repositories);
      setGitHubApp(status);
      setError(null);
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Repository connections could not be loaded.",
      );
    } finally {
      if (showLoading) setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (auth.status !== "authenticated") return;
    void loadWorkspace();
    return connectRepositoryStream(
      () => void loadWorkspace(false),
      setStream,
    );
  }, [auth.status, loadWorkspace]);

  const filteredRepositories = useMemo(() => {
    const term = search.trim().toLowerCase();
    return term
      ? connected.filter((repository) =>
          repository.fullName.toLowerCase().includes(term),
        )
      : connected;
  }, [connected, search]);

  const openManualConnection = async () => {
    setAdding(true);
    setError(null);
    setNotice(null);
    setSelected(null);
    setSelectedSource("");
    setBranches([]);
    setAvailable([]);
  };

  const selectSource = async (source: string) => {
    setSelectedSource(source);
    setSelected(null);
    setBranch("");
    setBranches([]);
    setError(null);
    const installationId = source === "oauth" ? undefined : Number(source);
    try {
      setAvailable(await getAvailableRepositories(installationId));
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Repositories for this GitHub source could not be loaded.",
      );
    }
  };

  const selectRepository = async (repository: AvailableRepository) => {
    setSelected(repository);
    setBranch(repository.defaultBranch);
    setError(null);
    try {
      setBranches(
        (
          await getRepositoryBranches(
            repository.githubRepositoryId,
            selectedSource === "oauth" ? undefined : Number(selectedSource),
          )
        ).map((item) => item.name),
      );
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Branches could not be loaded.",
      );
    }
  };

  const saveConnection = async () => {
    if (!selected || !branch) return;
    setBusy("manual");
    setError(null);
    try {
      await connectRepository(
        selected.githubRepositoryId,
        branch,
        selectedSource === "oauth" ? undefined : Number(selectedSource),
      );
      setAdding(false);
      setNotice(`${selected.fullName} is now monitored.`);
      await loadWorkspace(false);
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "The repository could not be connected.",
      );
    } finally {
      setBusy(null);
    }
  };

  const synchronize = async (installationId: number, account: string) => {
    setBusy(`sync-${installationId}`);
    setError(null);
    try {
      await synchronizeInstallation(installationId);
      await loadWorkspace(false);
      setNotice(`${account} was synchronized with GitHub.`);
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "The GitHub installation could not be synchronized.",
      );
    } finally {
      setBusy(null);
    }
  };

  const disconnectInstallation = async (
    installationId: number,
    account: string,
  ) => {
    if (
      !window.confirm(
        `Disconnect every repository synchronized from ${account}? The GitHub App will remain installed and can be reconnected later.`,
      )
    )
      return;
    setBusy(`disconnect-${installationId}`);
    setError(null);
    try {
      await disconnectInstallationRepositories(installationId);
      await loadWorkspace(false);
      setNotice(`Repositories from ${account} were disconnected.`);
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "The installation repositories could not be disconnected.",
      );
    } finally {
      setBusy(null);
    }
  };

  const disconnectAccount = async (
    installationId: number,
    account: string,
  ) => {
    if (
      !window.confirm(
        `Disconnect ${account}? This permanently uninstalls Repo Guardian from that GitHub account and stops its webhooks.`,
      )
    )
      return;
    setBusy(`account-${installationId}`);
    setError(null);
    try {
      await uninstallInstallation(installationId);
      await loadWorkspace(false);
      setNotice(`${account} was disconnected from Repo Guardian.`);
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "The GitHub account could not be disconnected.",
      );
    } finally {
      setBusy(null);
    }
  };

  const disconnectEverything = async () => {
    if (
      !window.confirm(
        `Disconnect all ${connected.length} repositories? GitHub App installations will remain available for later synchronization.`,
      )
    )
      return;
    setBusy("disconnect-all");
    setError(null);
    try {
      const result = await disconnectAllRepositories();
      await loadWorkspace(false);
      setNotice(`${result.disconnectedCount} repositories were disconnected.`);
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "The repositories could not be disconnected.",
      );
    } finally {
      setBusy(null);
    }
  };

  const removeConnection = async (repository: ConnectedRepository) => {
    if (!window.confirm(`Disconnect ${repository.fullName}?`)) return;
    setBusy(`repository-${repository.id}`);
    setError(null);
    try {
      await disconnectRepository(repository.id);
      await loadWorkspace(false);
      setNotice(`${repository.fullName} was disconnected.`);
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "The repository could not be disconnected.",
      );
    } finally {
      setBusy(null);
    }
  };

  const loadConnectionBranches = async (repository: ConnectedRepository) => {
    if (connectionBranches[repository.id]) return;
    try {
      const items = await getRepositoryBranches(repository.githubRepositoryId);
      setConnectionBranches((current) => ({
        ...current,
        [repository.id]: items.map((item) => item.name),
      }));
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Branches could not be loaded.",
      );
    }
  };

  const changeBranch = async (
    repository: ConnectedRepository,
    monitoredBranch: string,
  ) => {
    setBusy(`repository-${repository.id}`);
    setError(null);
    try {
      await updateRepository(repository.id, monitoredBranch);
      await loadWorkspace(false);
      setNotice(`${repository.fullName} now monitors ${monitoredBranch}.`);
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "The monitored branch could not be changed.",
      );
    } finally {
      setBusy(null);
    }
  };

  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Connections</p>
          <h1>Repositories</h1>
          <p>
            Manage GitHub sources and choose which branches Repo Guardian
            monitors. Build operations remain in the Builds workspace.
          </p>
        </div>
        {auth.status === "authenticated" ? (
          <span className={`live-status live-status--${stream}`}>
            <span aria-hidden="true" />
            {stream === "live" ? "GitHub updates live" : "Updates reconnecting"}
          </span>
        ) : null}
      </div>

      {auth.status !== "authenticated" ? (
        <AuthenticationState auth={auth} />
      ) : (
        <>
          {error ? (
            <div className="inline-alert" role="alert">
              {error}
            </div>
          ) : null}
          {notice ? (
            <div className="inline-notice" role="status">
              {notice}
            </div>
          ) : null}

          <section className="connection-overview" aria-labelledby="sources-title">
            <div className="section-heading">
              <div>
                <span className="step-label">GitHub sources</span>
                <h2 id="sources-title">Accounts and organizations</h2>
                <p>
                  Your GitHub login identifies you. Each GitHub App installation
                  grants repository access for a personal account or organization.
                </p>
              </div>
              {githubApp?.configured ? (
                <a className="primary-button" href="/api/github-app/install">
                  Add GitHub source
                </a>
              ) : null}
            </div>

            {!githubApp || loading ? (
              <div className="source-empty">Loading GitHub sources</div>
            ) : !githubApp.configured ? (
              <div className="source-empty">
                <h3>GitHub App configuration is required</h3>
                <p>Add the GitHub App environment variables before installing it.</p>
              </div>
            ) : githubApp.installations.length === 0 ? (
              <div className="source-empty">
                <h3>Install the GitHub App once per account</h3>
                <p>
                  Select all repositories for automatic synchronization, or
                  choose a controlled subset in GitHub.
                </p>
                <a className="primary-button" href="/api/github-app/install">
                  Install GitHub App
                </a>
              </div>
            ) : (
              <div className="source-grid">
                {githubApp.installations.map((installation) => (
                  <article
                    className="source-card"
                    key={installation.installationId}
                  >
                    <div className="source-card__identity">
                      <span className="source-avatar" aria-hidden="true">
                        {installation.accountLogin.slice(0, 1).toUpperCase()}
                      </span>
                      <div>
                        <h3>{installation.accountLogin}</h3>
                        <p>
                          {installation.accountType} · {installation.repositorySelection}
                          {" "}repositories
                        </p>
                      </div>
                      <span
                        className={`status-badge ${installation.monitoringEnabled ? "status-badge--connected" : "visibility-badge"}`}
                      >
                        {installation.monitoringEnabled
                          ? installation.status
                          : "disconnected"}
                      </span>
                    </div>
                    <div className="source-card__metric">
                      <strong>{installation.repositoryCount}</strong>
                      <span>repositories synchronized</span>
                    </div>
                    <p className="source-card__updated">
                      {installation.lastSyncedAt
                        ? `Last synchronized ${new Date(installation.lastSyncedAt).toLocaleString()}`
                        : "Not synchronized yet"}
                    </p>
                    <div className="source-card__actions">
                      <button
                        className="secondary-button"
                        type="button"
                        disabled={busy !== null}
                        onClick={() =>
                          void synchronize(
                            installation.installationId,
                            installation.accountLogin,
                          )
                        }
                      >
                        {busy === `sync-${installation.installationId}`
                          ? "Synchronizing..."
                          : installation.monitoringEnabled
                            ? "Synchronize now"
                            : "Reconnect repositories"}
                      </button>
                      <a
                        className="text-button"
                        href={`https://github.com/settings/installations/${installation.installationId}`}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Manage in GitHub
                      </a>
                      {installation.monitoringEnabled &&
                      installation.repositoryCount > 0 ? (
                        <button
                          className="text-button text-button--danger"
                          type="button"
                          disabled={busy !== null}
                          onClick={() =>
                            void disconnectInstallation(
                              installation.installationId,
                              installation.accountLogin,
                            )
                          }
                        >
                          Disconnect repositories
                        </button>
                      ) : null}
                      <button
                        className="text-button text-button--danger"
                        type="button"
                        disabled={busy !== null}
                        onClick={() =>
                          void disconnectAccount(
                            installation.installationId,
                            installation.accountLogin,
                          )
                        }
                      >
                        {busy === `account-${installation.installationId}`
                          ? "Disconnecting..."
                          : "Disconnect account"}
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>

          <section className="repository-section" aria-labelledby="repositories-title">
            <div className="section-heading repository-heading">
              <div>
                <h2 id="repositories-title">Monitored repositories</h2>
                <p>
                  {connected.length} {connected.length === 1 ? "repository" : "repositories"}
                  {githubApp ? ` across ${githubApp.installations.length} GitHub sources` : ""}
                </p>
              </div>
              <div className="repository-heading__actions">
                <button
                  className="secondary-button"
                  type="button"
                  onClick={() => void openManualConnection()}
                >
                  Add repository manually
                </button>
                {connected.length > 0 ? (
                  <button
                    className="danger-button"
                    type="button"
                    disabled={busy !== null}
                    onClick={() => void disconnectEverything()}
                  >
                    {busy === "disconnect-all"
                      ? "Disconnecting..."
                      : "Disconnect all"}
                  </button>
                ) : null}
              </div>
            </div>

            {adding ? (
              <div className="manual-connection" aria-labelledby="manual-title">
                <div className="panel-heading">
                  <div>
                    <span className="step-label">OAuth fallback</span>
                    <h3 id="manual-title">Connect one repository manually</h3>
                  </div>
                  <button
                    className="text-button"
                    type="button"
                    onClick={() => setAdding(false)}
                  >
                    Cancel
                  </button>
                </div>
                <div className="connection-form">
                  <label>
                    GitHub source
                    <select
                      value={selectedSource}
                      onChange={(event) => void selectSource(event.target.value)}
                    >
                      <option value="">Select an account or organization</option>
                      <option value="oauth">
                        {auth.user.githubUsername} (OAuth account)
                      </option>
                      {githubApp?.installations.map((installation) => (
                        <option
                          key={installation.installationId}
                          value={installation.installationId}
                        >
                          {installation.accountLogin} ({installation.accountType})
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Repository
                    <select
                      value={selected?.githubRepositoryId ?? ""}
                      disabled={!selectedSource}
                      onChange={(event) => {
                        const repository = available.find(
                          (item) =>
                            item.githubRepositoryId === Number(event.target.value),
                        );
                        if (repository) void selectRepository(repository);
                      }}
                    >
                      <option value="">Select a repository</option>
                      {available.map((item) => (
                        <option
                          key={item.githubRepositoryId}
                          value={item.githubRepositoryId}
                          disabled={item.isConnected}
                        >
                          {item.fullName}{item.isConnected ? " (connected)" : ""}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Monitored branch
                    <select
                      value={branch}
                      disabled={!selected || branches.length === 0}
                      onChange={(event) => setBranch(event.target.value)}
                    >
                      <option value="">Select a branch</option>
                      {branches.map((name) => (
                        <option key={name} value={name}>
                          {name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <button
                    className="primary-button"
                    type="button"
                    disabled={
                      !selectedSource || !selected || !branch || busy !== null
                    }
                    onClick={() => void saveConnection()}
                  >
                    {busy === "manual" ? "Connecting..." : "Connect repository"}
                  </button>
                </div>
              </div>
            ) : null}

            {connected.length > 4 ? (
              <label className="repository-search">
                <span>Search repositories</span>
                <input
                  type="search"
                  value={search}
                  placeholder="Filter by owner or repository"
                  onChange={(event) => setSearch(event.target.value)}
                />
              </label>
            ) : null}

            {loading && connected.length === 0 ? (
              <div className="empty-state"><h2>Loading repositories</h2></div>
            ) : connected.length === 0 ? (
              <div className="empty-state">
                <span>No monitored repositories</span>
                <h2>Connect a GitHub source to begin</h2>
                <p>
                  Synchronize an installation above, or use the manual fallback
                  for one repository.
                </p>
              </div>
            ) : filteredRepositories.length === 0 ? (
              <div className="empty-state"><h2>No repositories match your search</h2></div>
            ) : (
              <div className="repository-table-wrap">
                <table className="repository-table">
                  <thead>
                    <tr>
                      <th>Repository</th>
                      <th>Monitored branch</th>
                      <th>Webhook</th>
                      <th><span className="sr-only">Actions</span></th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredRepositories.map((repository) => (
                      <tr key={repository.id}>
                        <td>
                          <a href={repository.htmlUrl} target="_blank" rel="noreferrer">
                            {repository.fullName}
                          </a>
                          <small>
                            {repository.installationAccountLogin
                              ? `${repository.installationAccountLogin} · GitHub App`
                              : "Manually connected"}
                            {" · "}{repository.visibility}
                          </small>
                        </td>
                        <td>
                          <select
                            aria-label={`Monitored branch for ${repository.fullName}`}
                            value={repository.monitoredBranch}
                            disabled={busy === `repository-${repository.id}`}
                            onFocus={() => void loadConnectionBranches(repository)}
                            onChange={(event) =>
                              void changeBranch(repository, event.target.value)
                            }
                          >
                            {[
                              ...new Set([
                                repository.monitoredBranch,
                                repository.defaultBranch,
                                ...(connectionBranches[repository.id] ?? []),
                              ]),
                            ].map((name) => (
                              <option key={name} value={name}>{name}</option>
                            ))}
                          </select>
                        </td>
                        <td>
                          <span
                            className={`status-text ${repository.webhookStatus === "active" ? "status-text--active" : "status-text--pending"}`}
                          >
                            {repository.webhookStatus === "active"
                              ? "Active"
                              : repository.webhookStatus === "configured"
                                ? "Ready"
                                : "Not configured"}
                          </span>
                        </td>
                        <td>
                          <div className="row-actions">
                            <a className="text-button" href="/builds">View builds</a>
                            <button
                              className="text-button text-button--danger"
                              type="button"
                              disabled={busy !== null}
                              onClick={() => void removeConnection(repository)}
                            >
                              Disconnect
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      )}
    </>
  );
}
