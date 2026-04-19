def test_controller_can_edit_file_via_api(client):
    session_id = client.post(
        "/sessions",
        json={"repo_url": "https://github.com/example/repo.git"},
    ).json()["id"]
    client.post(f"/sessions/{session_id}/start")
    client.post(f"/sessions/{session_id}/control/claim", json={"user_id": "user-1"})

    edited = client.patch(
        f"/sessions/{session_id}/files/content",
        json={
            "user_id": "user-1",
            "path": "README.md",
            "content": "# Updated via API\n",
        },
    )
    content = client.get(
        f"/sessions/{session_id}/files/content",
        params={"path": "README.md"},
    )

    assert edited.status_code == 200
    assert content.status_code == 200
    assert content.json() == {"content": "# Updated via API\n"}


def test_non_controller_cannot_edit_file_via_api(client):
    session_id = client.post(
        "/sessions",
        json={"repo_url": "https://github.com/example/repo.git"},
    ).json()["id"]
    client.post(f"/sessions/{session_id}/start")
    client.post(f"/sessions/{session_id}/control/claim", json={"user_id": "user-1"})

    edited = client.patch(
        f"/sessions/{session_id}/files/content",
        json={
            "user_id": "user-2",
            "path": "README.md",
            "content": "# Unauthorized\n",
        },
    )

    assert edited.status_code == 403
    assert edited.json() == {"detail": "only controller can edit files"}
