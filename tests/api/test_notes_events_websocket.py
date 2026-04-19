from tests.helpers.websocket import receive_json_with_timeout


def test_watcher_receives_note_added_event_over_websocket(client):
    session_id = client.post(
        "/sessions",
        json={"repo_url": "https://github.com/example/repo.git"},
    ).json()["id"]

    with client.websocket_connect(f"/sessions/{session_id}/events/ws") as websocket:
        created = client.post(
            f"/sessions/{session_id}/notes",
            json={"author_id": "user-2", "body": "looks good"},
        )

        message = receive_json_with_timeout(websocket)

    assert created.status_code == 200
    assert message == {
        "type": "note_added",
        "session_id": session_id,
        "author_id": "user-2",
        "body": "looks good",
        "created_at": 1,
    }
