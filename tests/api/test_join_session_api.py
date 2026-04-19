def test_viewer_can_join_session_via_api(client):
    session_id = client.post(
        "/sessions",
        json={"repo_url": "https://github.com/example/repo.git"},
    ).json()["id"]

    joined = client.post(
        f"/sessions/{session_id}/join",
        json={"user_id": "viewer-1"},
    )

    assert joined.status_code == 200
    assert joined.json()["viewers"] == ["viewer-1"]
