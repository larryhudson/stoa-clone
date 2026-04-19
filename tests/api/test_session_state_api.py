def test_can_fetch_session_state_via_api(client):
    created = client.post(
        "/sessions",
        json={"repo_url": "https://github.com/example/repo.git", "branch": "main"},
    )
    session_id = created.json()["id"]

    fetched = client.get(f"/sessions/{session_id}")

    assert fetched.status_code == 200
    assert fetched.json() == {
        "id": session_id,
        "repo_url": "https://github.com/example/repo.git",
        "branch": "main",
        "status": "created",
        "workspace_path": None,
        "controller_id": None,
        "viewers": [],
    }
