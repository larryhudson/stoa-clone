def test_hidden_paths_are_not_listed_or_accessible_via_api(client, tmp_path):
    source_repo = tmp_path / "source-repo"
    source_repo.mkdir()

    _run(["git", "init", "-b", "main"], cwd=source_repo)
    (source_repo / "README.md").write_text("# Real repo\n")
    _run(["git", "add", "README.md"], cwd=source_repo)
    _run(
        [
            "git",
            "-c",
            "user.name=Test User",
            "-c",
            "user.email=test@example.com",
            "commit",
            "-m",
            "initial",
        ],
        cwd=source_repo,
    )

    created = client.post(
        "/sessions",
        json={"repo_url": str(source_repo), "branch": "main"},
    )
    session_id = created.json()["id"]
    client.post(f"/sessions/{session_id}/start")

    files = client.get(f"/sessions/{session_id}/files")
    hidden = client.get(
        f"/sessions/{session_id}/files/content",
        params={"path": ".git/HEAD"},
    )

    assert files.status_code == 200
    assert "README.md" in files.json()
    assert all(not path.startswith(".git/") for path in files.json())
    assert hidden.status_code == 400


def _run(command: list[str], cwd):
    import subprocess

    subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True)
