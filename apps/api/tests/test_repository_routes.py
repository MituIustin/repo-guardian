def test_repository_endpoints_require_authentication(client) -> None:
    assert client.get("/api/repositories").status_code == 401
    assert client.get("/api/repositories/available").status_code == 401
    assert client.post(
        "/api/repositories/connect",
        json={"githubRepositoryId": 42, "monitoredBranch": "main"},
    ).status_code == 401
    assert client.delete("/api/repositories").status_code == 401
