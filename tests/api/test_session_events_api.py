def test_can_fetch_session_event_history_via_api(client):
    session_id = client.post(
        "/sessions",
        json={"repo_url": "https://github.com/example/repo.git"},
    ).json()["id"]
    client.post(f"/sessions/{session_id}/join", json={"user_id": "viewer-1"})
    client.post(
        f"/sessions/{session_id}/notes",
        json={"author_id": "user-2", "body": "looks good"},
    )

    fetched = client.get(f"/sessions/{session_id}/events")

    assert fetched.status_code == 200
    assert fetched.json() == [
        {
            "type": "viewer_joined",
            "session_id": session_id,
            "user_id": "viewer-1",
        },
        {
            "type": "note_added",
            "session_id": session_id,
            "author_id": "user-2",
            "body": "looks good",
            "created_at": 1,
        },
    ]
