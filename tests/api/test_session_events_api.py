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


def test_agent_prompt_submission_is_recorded_in_event_history(client):
    session_id = client.post(
        "/sessions",
        json={"repo_url": "https://github.com/example/repo.git"},
    ).json()["id"]
    client.post(f"/sessions/{session_id}/start")
    client.post(f"/sessions/{session_id}/control/claim", json={"user_id": "user-1"})
    client.post(
        f"/sessions/{session_id}/agent/prompt",
        json={"user_id": "user-1", "text": "Summarize this repository"},
    )

    fetched = client.get(f"/sessions/{session_id}/events")

    assert fetched.status_code == 200
    assert fetched.json()[-1] == {
        "type": "agent_prompt_submitted",
        "session_id": session_id,
        "user_id": "user-1",
        "text": "Summarize this repository",
    }
