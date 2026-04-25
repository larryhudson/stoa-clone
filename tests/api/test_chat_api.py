from tests.helpers.websocket import receive_json_with_timeout


def test_joined_viewer_can_post_and_list_chat_messages_via_api(client):
    session_id = client.post(
        "/sessions",
        json={"repo_url": "https://github.com/example/repo.git"},
    ).json()["id"]
    client.post(f"/sessions/{session_id}/join", json={"user_id": "user-1"})

    posted = client.post(
        f"/sessions/{session_id}/chat",
        json={"author_id": "user-1", "body": "Let's build a meeting transcript."},
    )
    listed = client.get(f"/sessions/{session_id}/chat")

    assert posted.status_code == 200
    assert listed.json() == [
        {
            "id": posted.json()["id"],
            "author_id": "user-1",
            "body": "Let's build a meeting transcript.",
            "created_at": posted.json()["created_at"],
        }
    ]


def test_chat_message_is_streamed_over_websocket(client):
    session_id = client.post(
        "/sessions",
        json={"repo_url": "https://github.com/example/repo.git"},
    ).json()["id"]
    client.post(f"/sessions/{session_id}/join", json={"user_id": "user-1"})

    with client.websocket_connect(f"/sessions/{session_id}/events/ws") as websocket:
        posted = client.post(
            f"/sessions/{session_id}/chat",
            json={"author_id": "user-1", "body": "Let's build a meeting transcript."},
        )
        message = receive_json_with_timeout(websocket)

    assert posted.status_code == 200
    assert message == {
        "type": "chat_message_added",
        "session_id": session_id,
        "message_id": posted.json()["id"],
        "author_id": "user-1",
        "body": "Let's build a meeting transcript.",
        "created_at": posted.json()["created_at"],
    }


def test_non_viewer_cannot_post_chat_via_api(client):
    session_id = client.post(
        "/sessions",
        json={"repo_url": "https://github.com/example/repo.git"},
    ).json()["id"]

    posted = client.post(
        f"/sessions/{session_id}/chat",
        json={"author_id": "user-1", "body": "hello"},
    )

    assert posted.status_code == 403
    assert posted.json() == {"detail": "only joined viewers can post chat messages"}
