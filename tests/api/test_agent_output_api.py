def test_session_state_includes_accumulated_agent_output(client):
    session_id = client.post(
        "/sessions",
        json={"repo_url": "https://github.com/example/repo.git"},
    ).json()["id"]
    client.post(f"/sessions/{session_id}/start")

    app = client.app
    app.state.container.session_service.record_runtime_event(
        session_id,
        {"type": "agent_text_delta", "session_id": session_id, "delta": "Hello"},
    )
    app.state.container.session_service.record_runtime_event(
        session_id,
        {"type": "agent_text_delta", "session_id": session_id, "delta": " world"},
    )

    fetched = client.get(f"/sessions/{session_id}")

    assert fetched.status_code == 200
    assert fetched.json()["agent_output"] == "Hello world"
    assert fetched.json()["agent_output_status"] == "streaming"
    assert fetched.json()["agent_output_error"] is None


def test_session_state_includes_failed_agent_output_metadata(client):
    session_id = client.post(
        "/sessions",
        json={"repo_url": "https://github.com/example/repo.git"},
    ).json()["id"]
    client.post(f"/sessions/{session_id}/start")

    app = client.app
    app.state.container.session_service.record_runtime_event(
        session_id,
        {
            "type": "agent_run_failed",
            "session_id": session_id,
            "error": "No API key found",
        },
    )

    fetched = client.get(f"/sessions/{session_id}")

    assert fetched.status_code == 200
    assert fetched.json()["agent_output"] == ""
    assert fetched.json()["agent_output_status"] == "failed"
    assert fetched.json()["agent_output_error"] == "No API key found"
