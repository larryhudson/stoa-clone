from tests.helpers.websocket import receive_json_with_timeout


def test_watcher_receives_viewer_left_event_when_viewer_disconnects(client):
    session_id = client.post(
        "/sessions",
        json={"repo_url": "https://github.com/example/repo.git"},
    ).json()["id"]
    client.post(f"/sessions/{session_id}/join", json={"user_id": "viewer-1"})

    with client.websocket_connect(f"/sessions/{session_id}/events/ws") as watcher:
        with client.websocket_connect(f"/sessions/{session_id}/events/ws?user_id=viewer-1"):
            pass

        message = receive_json_with_timeout(watcher)

    assert message == {
        "type": "viewer_left",
        "session_id": session_id,
        "user_id": "viewer-1",
    }

    presence = client.get(f"/sessions/{session_id}/presence")
    assert presence.status_code == 200
    assert presence.json() == {
        "controller_id": None,
        "viewers": [],
    }
