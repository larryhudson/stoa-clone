from tests.helpers.websocket import receive_json_with_timeout


def test_watcher_receives_control_claimed_event_over_websocket(client):
    session_id = client.post(
        "/sessions",
        json={"repo_url": "https://github.com/example/repo.git"},
    ).json()["id"]

    with client.websocket_connect(f"/sessions/{session_id}/events/ws") as websocket:
        claimed = client.post(
            f"/sessions/{session_id}/control/claim",
            json={"user_id": "user-1"},
        )

        message = receive_json_with_timeout(websocket)

    assert claimed.status_code == 200
    assert message == {
        "type": "control_claimed",
        "session_id": session_id,
        "user_id": "user-1",
    }
