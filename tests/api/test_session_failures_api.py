def test_start_session_failure_returns_500_and_marks_session_failed(make_failing_client):
    failing_client, store = make_failing_client(
        provision_error=RuntimeError("clone failed")
    )

    session_id = failing_client.post(
        "/sessions",
        json={"repo_url": "https://github.com/example/repo.git"},
    ).json()["id"]

    started = failing_client.post(f"/sessions/{session_id}/start")

    assert started.status_code == 500
    assert started.json() == {"detail": "clone failed"}
    assert store.get(session_id).status.value == "failed"
