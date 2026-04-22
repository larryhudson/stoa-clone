def test_can_create_and_start_session_via_api(client):

    created = client.post(
        "/sessions",
        json={"repo_url": "https://github.com/example/repo.git", "branch": "main"},
    )
    session_id = created.json()["id"]
    started = client.post(f"/sessions/{session_id}/start")

    assert created.status_code == 200
    assert started.status_code == 200
    assert started.json()["status"] == "ready"
    assert started.json()["agent_session_id"] == f"agent-{session_id}"
    assert started.json()["agent_status"] == "idle"


def test_control_conflict_returns_409(client):
    session_id = client.post(
        "/sessions", json={"repo_url": "https://github.com/example/repo.git"}
    ).json()["id"]

    first = client.post(f"/sessions/{session_id}/control/claim", json={"user_id": "u1"})
    second = client.post(f"/sessions/{session_id}/control/claim", json={"user_id": "u2"})

    assert first.status_code == 200
    assert second.status_code == 409


def test_can_browse_files_and_preview_markdown_via_api(client):
    session_id = client.post(
        "/sessions", json={"repo_url": "https://github.com/example/repo.git"}
    ).json()["id"]
    client.post(f"/sessions/{session_id}/start")

    files = client.get(f"/sessions/{session_id}/files")
    content = client.get(f"/sessions/{session_id}/files/content", params={"path": "README.md"})
    preview = client.get(f"/sessions/{session_id}/files/preview", params={"path": "README.md"})

    assert files.status_code == 200
    assert "README.md" in files.json()
    assert "Cloned repo" in content.json()["content"]
    assert "<h1>Cloned repo</h1>" in preview.json()["html"]
