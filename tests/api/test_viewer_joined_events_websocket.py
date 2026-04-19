from tests.helpers.websocket import receive_json_with_timeout


def test_watcher_receives_viewer_joined_event_over_websocket(client):
    session_id = client.post(
        "/sessions",
        json={"repo_url": "https://github.com/example/repo.git"},
    ).json()["id"]

    with client.websocket_connect(f"/sessions/{session_id}/events/ws") as websocket:
        joined = client.post(
            f"/sessions/{session_id}/join",
            json={"user_id": "viewer-1"},
        )

        message = receive_json_with_timeout(websocket)

    assert joined.status_code == 200
    assert message == {
        "type": "viewer_joined",
        "session_id": session_id,
        "user_id": "viewer-1",
    }
