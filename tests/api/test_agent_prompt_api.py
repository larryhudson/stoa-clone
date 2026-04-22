def test_controller_can_submit_prompt_to_agent_via_api(client):
    session_id = client.post(
        "/sessions",
        json={"repo_url": "https://github.com/example/repo.git"},
    ).json()["id"]
    client.post(f"/sessions/{session_id}/start")
    client.post(f"/sessions/{session_id}/control/claim", json={"user_id": "user-1"})

    prompted = client.post(
        f"/sessions/{session_id}/agent/prompt",
        json={"user_id": "user-1", "text": "Summarize this repository"},
    )

    assert prompted.status_code == 200
    assert prompted.json()["agent_status"] == "running"
    assert prompted.json()["agent_session_id"] == f"agent-{session_id}"



def test_non_controller_cannot_submit_prompt_to_agent_via_api(client):
    session_id = client.post(
        "/sessions",
        json={"repo_url": "https://github.com/example/repo.git"},
    ).json()["id"]
    client.post(f"/sessions/{session_id}/start")

    prompted = client.post(
        f"/sessions/{session_id}/agent/prompt",
        json={"user_id": "user-2", "text": "Summarize this repository"},
    )

    assert prompted.status_code == 403
    assert prompted.json() == {"detail": "only controller can prompt agent"}



def test_controller_can_steer_and_abort_agent_via_api(client):
    session_id = client.post(
        "/sessions",
        json={"repo_url": "https://github.com/example/repo.git"},
    ).json()["id"]
    client.post(f"/sessions/{session_id}/start")
    client.post(f"/sessions/{session_id}/control/claim", json={"user_id": "user-1"})
    client.post(
        f"/sessions/{session_id}/agent/prompt",
        json={"user_id": "user-1", "text": "Summarize this repository"},
    )

    steered = client.post(
        f"/sessions/{session_id}/agent/steer",
        json={"user_id": "user-1", "text": "Focus on tests"},
    )
    aborted = client.post(
        f"/sessions/{session_id}/agent/abort",
        json={"user_id": "user-1"},
    )

    assert steered.status_code == 200
    assert steered.json()["agent_status"] == "running"
    assert aborted.status_code == 200
    assert aborted.json()["agent_status"] == "idle"
