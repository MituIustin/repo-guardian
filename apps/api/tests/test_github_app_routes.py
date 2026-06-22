def test_github_app_endpoints_require_authentication(client) -> None:
    assert client.get("/api/github-app/status").status_code == 401
    assert client.get("/api/github-app/install", follow_redirects=False).status_code == 401
    assert client.post("/api/github-app/installations/77/synchronize").status_code == 401
    assert client.delete("/api/github-app/installations/77/repositories").status_code == 401
    assert client.delete("/api/github-app/installations/77").status_code == 401
