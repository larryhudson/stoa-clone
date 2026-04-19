def test_can_fetch_session_presence_via_api(client):
    session_id = client.post(
        "/sessions",
        json={"repo_url": "https://github.com/example/repo.git"},
    ).json()["id"]
    client.post(f"/sessions/{session_id}/join", json={"user_id": "viewer-1"})
    client.post(f"/sessions/{session_id}/control/claim", json={"user_id": "user-1"})

    fetched = client.get(f"/sessions/{session_id}/presence")

    assert fetched.status_code == 200
    assert fetched.json() == {
        "controller_id": "user-1",
        "viewers": ["user-1", "viewer-1"],
    }
