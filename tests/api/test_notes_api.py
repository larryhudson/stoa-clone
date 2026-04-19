def test_any_viewer_can_add_notes_via_api(client):
    session_id = client.post(
        "/sessions",
        json={"repo_url": "https://github.com/example/repo.git"},
    ).json()["id"]

    first = client.post(
        f"/sessions/{session_id}/notes",
        json={"author_id": "user-1", "body": "watching this"},
    )
    second = client.post(
        f"/sessions/{session_id}/notes",
        json={"author_id": "user-2", "body": "looks good"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == {
        "author_id": "user-1",
        "body": "watching this",
        "created_at": 1,
    }
    assert second.json() == {
        "author_id": "user-2",
        "body": "looks good",
        "created_at": 2,
    }
