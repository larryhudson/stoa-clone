def test_file_edit_event_is_available_in_session_event_history(client):
    session_id = client.post(
        "/sessions",
        json={"repo_url": "https://github.com/example/repo.git"},
    ).json()["id"]
    client.post(f"/sessions/{session_id}/start")
    client.post(f"/sessions/{session_id}/control/claim", json={"user_id": "user-1"})
    client.patch(
        f"/sessions/{session_id}/files/content",
        json={
            "user_id": "user-1",
            "path": "README.md",
            "content": "# Updated via API\n",
        },
    )

    fetched = client.get(f"/sessions/{session_id}/events")

    assert fetched.status_code == 200
    assert fetched.json()[-1] == {
        "type": "file_edited",
        "session_id": session_id,
        "path": "README.md",
        "editor_id": "user-1",
        "content": "# Updated via API\n",
    }
