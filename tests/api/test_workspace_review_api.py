def test_workspace_review_endpoint_returns_changed_files_and_diff(client):
    session_id = client.post(
        "/sessions",
        json={"repo_url": "https://github.com/example/repo.git"},
    ).json()["id"]
    client.post(f"/sessions/{session_id}/start")
    client.post(f"/sessions/{session_id}/join", json={"user_id": "user-1"})
    client.post(f"/sessions/{session_id}/control/claim", json={"user_id": "user-1"})
    client.patch(
        f"/sessions/{session_id}/files/content",
        json={
            "user_id": "user-1",
            "path": "README.md",
            "content": "# Changed\n",
        },
    )

    reviewed = client.get(f"/sessions/{session_id}/workspace/review")

    assert reviewed.status_code == 200
    assert reviewed.json()["changed_files"] == ["README.md"]
    assert "# Changed" in reviewed.json()["diff"]
