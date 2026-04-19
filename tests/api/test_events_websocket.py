from tests.helpers.websocket import receive_json_with_timeout


def test_watcher_receives_file_edited_event_over_websocket(client):
    session_id = client.post(
        "/sessions",
        json={"repo_url": "https://github.com/example/repo.git"},
    ).json()["id"]
    client.post(f"/sessions/{session_id}/start")
    client.post(f"/sessions/{session_id}/control/claim", json={"user_id": "user-1"})

    with client.websocket_connect(f"/sessions/{session_id}/events/ws") as websocket:
        client.patch(
            f"/sessions/{session_id}/files/content",
            json={
                "user_id": "user-1",
                "path": "README.md",
                "content": "# Updated via websocket\n",
            },
        )

        message = receive_json_with_timeout(websocket)

    assert message == {
        "type": "file_edited",
        "session_id": session_id,
        "path": "README.md",
        "editor_id": "user-1",
        "content": "# Updated via websocket\n",
    }
