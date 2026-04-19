def test_can_fetch_notes_for_session_via_api(client):
    session_id = client.post(
        "/sessions",
        json={"repo_url": "https://github.com/example/repo.git"},
    ).json()["id"]
    client.post(
        f"/sessions/{session_id}/notes",
        json={"author_id": "user-1", "body": "watching this"},
    )
    client.post(
        f"/sessions/{session_id}/notes",
        json={"author_id": "user-2", "body": "looks good"},
    )

    fetched = client.get(f"/sessions/{session_id}/notes")

    assert fetched.status_code == 200
    assert fetched.json() == [
        {"author_id": "user-1", "body": "watching this", "created_at": 1},
        {"author_id": "user-2", "body": "looks good", "created_at": 2},
    ]
