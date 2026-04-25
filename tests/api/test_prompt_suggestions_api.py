from tests.helpers.websocket import receive_json_with_timeout


def test_session_snapshot_exposes_pending_prompt_suggestions(client):
    session_id = _ready_session_with_controller(client)

    client.post(
        f"/sessions/{session_id}/chat",
        json={"author_id": "user-1", "body": "Let's add meeting chat."},
    )
    snapshot = client.get(f"/sessions/{session_id}").json()

    assert snapshot["prompt_suggestions"] == [
        {
            "id": snapshot["prompt_suggestions"][0]["id"],
            "text": "Add hello world to the README.",
            "reason": "A meeting message described implementation intent.",
            "source_message_ids": [snapshot["chat_messages"][0]["id"]],
            "status": "pending",
            "created_at": snapshot["prompt_suggestions"][0]["created_at"],
        }
    ]


def test_controller_accepts_prompt_suggestion_via_api(client):
    session_id = _ready_session_with_controller(client)
    client.post(
        f"/sessions/{session_id}/chat",
        json={"author_id": "user-1", "body": "Let's add meeting chat."},
    )
    suggestion_id = client.get(f"/sessions/{session_id}").json()["prompt_suggestions"][0]["id"]

    accepted = client.post(
        f"/sessions/{session_id}/prompt-suggestions/{suggestion_id}/accept",
        json={"user_id": "user-1"},
    )

    assert accepted.status_code == 200
    assert accepted.json()["prompt_suggestions"][0]["status"] == "accepted"
    assert accepted.json()["agent_status"] == "running"


def test_accepting_prompt_suggestion_submits_the_suggestion_to_agent_runtime(
    client,
    agent_runtime,
):
    session_id = _ready_session_with_controller(client)
    client.post(
        f"/sessions/{session_id}/chat",
        json={"author_id": "user-1", "body": "Let's add meeting chat."},
    )
    suggestion = client.get(f"/sessions/{session_id}").json()["prompt_suggestions"][0]

    accepted = client.post(
        f"/sessions/{session_id}/prompt-suggestions/{suggestion['id']}/accept",
        json={"user_id": "user-1"},
    )
    events = client.get(f"/sessions/{session_id}/events").json()

    assert accepted.status_code == 200
    assert agent_runtime.prompt_calls == [
        (f"agent-{session_id}", suggestion["text"]),
    ]
    assert events[-1] == {
        "type": "agent_prompt_submitted",
        "session_id": session_id,
        "user_id": "user-1",
        "text": suggestion["text"],
    }


def test_non_controller_cannot_accept_prompt_suggestion_via_api(client):
    session_id = _ready_session_with_controller(client)
    client.post(f"/sessions/{session_id}/join", json={"user_id": "user-2"})
    client.post(
        f"/sessions/{session_id}/chat",
        json={"author_id": "user-1", "body": "Let's add meeting chat."},
    )
    suggestion_id = client.get(f"/sessions/{session_id}").json()["prompt_suggestions"][0]["id"]

    accepted = client.post(
        f"/sessions/{session_id}/prompt-suggestions/{suggestion_id}/accept",
        json={"user_id": "user-2"},
    )

    assert accepted.status_code == 403
    assert accepted.json() == {"detail": "only controller can manage prompt suggestions"}


def test_controller_dismisses_prompt_suggestion_via_api(client):
    session_id = _ready_session_with_controller(client)
    client.post(
        f"/sessions/{session_id}/chat",
        json={"author_id": "user-1", "body": "Let's add meeting chat."},
    )
    suggestion_id = client.get(f"/sessions/{session_id}").json()["prompt_suggestions"][0]["id"]

    dismissed = client.post(
        f"/sessions/{session_id}/prompt-suggestions/{suggestion_id}/dismiss",
        json={"user_id": "user-1"},
    )

    assert dismissed.status_code == 200
    assert dismissed.json()["prompt_suggestions"][0]["status"] == "dismissed"


def test_prompt_suggestion_events_stream_over_websocket(client):
    session_id = _ready_session_with_controller(client)

    with client.websocket_connect(f"/sessions/{session_id}/events/ws") as websocket:
        client.post(
            f"/sessions/{session_id}/chat",
            json={"author_id": "user-1", "body": "Let's add meeting chat."},
        )
        receive_json_with_timeout(websocket)
        suggested = receive_json_with_timeout(websocket)
        suggestion_id = suggested["suggestion_id"]

        client.post(
            f"/sessions/{session_id}/prompt-suggestions/{suggestion_id}/dismiss",
            json={"user_id": "user-1"},
        )
        dismissed = receive_json_with_timeout(websocket)

    assert suggested["type"] == "agent_prompt_suggested"
    assert suggested["text"] == "Add hello world to the README."
    assert dismissed == {
        "type": "agent_prompt_suggestion_dismissed",
        "session_id": session_id,
        "suggestion_id": suggestion_id,
        "user_id": "user-1",
    }


def _ready_session_with_controller(client):
    session_id = client.post(
        "/sessions",
        json={"repo_url": "https://github.com/example/repo.git"},
    ).json()["id"]
    client.post(f"/sessions/{session_id}/start")
    client.post(f"/sessions/{session_id}/join", json={"user_id": "user-1"})
    client.post(f"/sessions/{session_id}/control/claim", json={"user_id": "user-1"})
    return session_id
