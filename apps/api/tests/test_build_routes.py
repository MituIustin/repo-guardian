import uuid


def test_build_rerun_endpoints_require_authentication(client) -> None:
    build_id = uuid.uuid4()
    job_id = uuid.uuid4()

    assert client.post(
        f"/api/builds/{build_id}/rerun", json={"mode": "all"}
    ).status_code == 401
    assert client.post(f"/api/builds/jobs/{job_id}/rerun").status_code == 401
