import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App";

const jsonResponse = (body: unknown, status = 200) =>
  Promise.resolve(
    new Response(JSON.stringify(body), {
      status,
      headers: { "Content-Type": "application/json" },
    }),
  );

afterEach(() => vi.unstubAllGlobals());

describe("dashboard", () => {
  it("shows navigation and an authentication message without account data", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => jsonResponse({ detail: "Not authenticated." }, 401)),
    );
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>,
    );

    expect(
      screen.getByRole("navigation", { name: "Primary navigation" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Repositories" }),
    ).toBeInTheDocument();
    expect(
      await screen.findByRole("heading", {
        name: "Sign in to use this workspace",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByRole("link", { name: /GitHub/i }).length,
    ).toBeGreaterThan(0);
  });

  it("renders the authenticated dashboard identity", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        jsonResponse({
          id: "user-id",
          name: "Ada Developer",
          email: "ada@example.com",
          avatarUrl: null,
          githubUsername: "ada-dev",
        }),
      ),
    );
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>,
    );

    expect(
      await screen.findByText("Welcome, Ada Developer"),
    ).toBeInTheDocument();
    expect(screen.getByText("@ada-dev")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Sign out" }),
    ).toBeInTheDocument();
  });

  it("loads connected repositories and identifies deferred information", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url === "/api/auth/me")
        return jsonResponse({
          id: "user-id",
          name: "Ada Developer",
          email: null,
          avatarUrl: null,
          githubUsername: "ada-dev",
        });
      if (url === "/api/repositories")
        return jsonResponse({
          data: [
            {
              id: "repository-id",
              githubRepositoryId: 42,
              name: "guardian",
              fullName: "ada-dev/guardian",
              visibility: "private",
              htmlUrl: "https://github.com/ada-dev/guardian",
              defaultBranch: "main",
              monitoredBranch: "main",
              isActive: true,
              webhookStatus: "not_configured",
              connectedAt: "2026-06-21T12:00:00Z",
            },
          ],
        });
      if (url === "/api/github-app/status")
        return jsonResponse({
          configured: true,
          installed: true,
          totalRepositoryCount: 1,
          installations: [
            {
              installationId: 77,
              accountLogin: "ada-dev",
              accountType: "User",
              repositorySelection: "all",
              status: "active",
              monitoringEnabled: true,
              repositoryCount: 1,
              lastSyncedAt: "2026-06-22T12:00:00Z",
            },
          ],
        });
      return jsonResponse({ detail: "Unexpected request" }, 500);
    });
    vi.stubGlobal("fetch", fetchMock);
    render(
      <MemoryRouter initialEntries={["/repositories"]}>
        <App />
      </MemoryRouter>,
    );

    expect(
      await screen.findByRole("link", { name: "ada-dev/guardian" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /^ada-dev$/ }),
    ).toBeInTheDocument();
    expect(screen.getByText("Not configured")).toBeInTheDocument();
    expect(screen.getByText("View builds")).toBeInTheDocument();
  });

  it("opens the repository connection flow", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url === "/api/auth/me")
        return jsonResponse({
          id: "user-id",
          name: "Ada",
          email: null,
          avatarUrl: null,
          githubUsername: "ada",
        });
      if (url === "/api/repositories") return jsonResponse({ data: [] });
      if (url === "/api/github-app/status")
        return jsonResponse({
          configured: true,
          installed: false,
          totalRepositoryCount: 0,
          installations: [],
        });
      if (url === "/api/repositories/available")
        return jsonResponse({
          data: [
            {
              githubRepositoryId: 7,
              name: "project",
              fullName: "ada/project",
              private: false,
              visibility: "public",
              htmlUrl: "https://github.com/ada/project",
              defaultBranch: "main",
              updatedAt: "2026-06-21T12:00:00Z",
              isConnected: false,
            },
          ],
        });
      if (url.includes("/branches"))
        return jsonResponse({ data: [{ name: "main" }, { name: "develop" }] });
      return jsonResponse({ detail: "Unexpected request" }, 500);
    });
    vi.stubGlobal("fetch", fetchMock);
    render(
      <MemoryRouter initialEntries={["/repositories"]}>
        <App />
      </MemoryRouter>,
    );

    await screen.findByText("Connect a GitHub source to begin");
    fireEvent.click(
      screen.getByRole("button", { name: "Add repository manually" }),
    );
    fireEvent.change(screen.getByLabelText("GitHub source"), {
      target: { value: "oauth" },
    });
    const repositorySelect = await screen.findByLabelText("Repository");
    fireEvent.change(repositorySelect, { target: { value: "7" } });
    await waitFor(() =>
      expect(screen.getByLabelText("Monitored branch")).toHaveValue("main"),
    );
    expect(screen.getByRole("option", { name: "develop" })).toBeInTheDocument();
  });

  it("shows real failed build evidence", async () => {
    class MockWebSocket {
      static OPEN = 1;
      readyState = 1;
      addEventListener() {}
      send() {}
      close() {}
    }
    vi.stubGlobal("WebSocket", MockWebSocket);
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        if (String(input) === "/api/auth/me")
          return jsonResponse({
            id: "user-id",
            name: "Ada",
            email: null,
            avatarUrl: null,
            githubUsername: "ada",
          });
        if (String(input) === "/api/builds")
          return jsonResponse({
            data: [
              {
                id: "build-id",
                repositoryId: "repository-id",
                repositoryFullName: "ada/project",
                githubRunId: 42,
                workflowName: "CI",
                runNumber: 12,
                runAttempt: 1,
                branch: "main",
                commitSha: "abcdef123456",
                status: "completed",
                conclusion: "failure",
                event: "push",
                htmlUrl: "https://github.com/ada/project/actions/runs/42",
                startedAt: "2026-06-22T10:00:00Z",
                completedAt: "2026-06-22T10:01:00Z",
                updatedAt: "2026-06-22T10:01:00Z",
                jobs: [],
                errorExcerpt: {
                  sourceFile: "test.txt",
                  startLine: 10,
                  endLine: 12,
                  content: "ERROR: test failed",
                },
              },
            ],
          });
        return jsonResponse({ detail: "Unexpected request" }, 500);
      }),
    );

    render(
      <MemoryRouter initialEntries={["/builds"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByText("CI")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Details/ }));
    expect(screen.getAllByText("Failed").length).toBeGreaterThan(0);
    expect(screen.getByText("ERROR: test failed")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Open in GitHub" }),
    ).toHaveAttribute("href", "https://github.com/ada/project/actions/runs/42");
    expect(
      screen.getByRole("button", { name: "Rerun failed jobs" }),
    ).toBeInTheDocument();
  });
});
