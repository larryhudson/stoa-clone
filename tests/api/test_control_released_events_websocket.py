from tests.helpers.websocket import receive_json_with_timeout


def test_watcher_receives_control_released_event_over_websocket(client):
    session_id = client.post(
        "/sessions",
        json={"repo_url": "https://github.com/example/repo.git"},
    ).json()["id"]
    client.post(f"/sessions/{session_id}/control/claim", json={"user_id": "user-1"})

    with client.websocket_connect(f"/sessions/{session_id}/events/ws") as websocket:
        released = client.post(
            f"/sessions/{session_id}/control/release",
            json={"user_id": "user-1"},
        )

        message = receive_json_with_timeout(websocket)

    assert released.status_code == 200
    assert message == {
        "type": "control_released",
        "session_id": session_id,
        "user_id": "user-1",
    }
