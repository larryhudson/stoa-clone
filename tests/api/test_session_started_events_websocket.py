from tests.helpers.websocket import receive_json_with_timeout


def test_watcher_receives_session_started_event_over_websocket(client):
    session_id = client.post(
        "/sessions",
        json={"repo_url": "https://github.com/example/repo.git"},
    ).json()["id"]

    with client.websocket_connect(f"/sessions/{session_id}/events/ws") as websocket:
        started = client.post(f"/sessions/{session_id}/start")
        message = receive_json_with_timeout(websocket)

    assert started.status_code == 200
    assert message == {
        "type": "session_started",
        "session_id": session_id,
        "workspace_path": started.json()["workspace_path"],
        "agent_session_id": started.json()["agent_session_id"],
    }
