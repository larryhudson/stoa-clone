from tests.helpers.websocket import receive_json_with_timeout


def test_watcher_receives_session_failed_event_over_websocket(make_failing_client):
    failing_client, _store = make_failing_client(provision_error=RuntimeError("clone failed"))

    session_id = failing_client.post(
        "/sessions",
        json={"repo_url": "https://github.com/example/repo.git"},
    ).json()["id"]

    with failing_client.websocket_connect(f"/sessions/{session_id}/events/ws") as websocket:
        started = failing_client.post(f"/sessions/{session_id}/start")
        message = receive_json_with_timeout(websocket)

    assert started.status_code == 500
    assert message == {
        "type": "session_failed",
        "session_id": session_id,
        "error": "clone failed",
    }
