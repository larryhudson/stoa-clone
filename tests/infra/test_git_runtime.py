from pathlib import Path

from app.infra.git_runtime import GitRuntime


def test_git_runtime_clones_local_repository(tmp_path):
    source_repo = tmp_path / "source-repo"
    source_repo.mkdir()

    _run(
        ["git", "init", "-b", "main"],
        cwd=source_repo,
    )
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

    runtime = GitRuntime(tmp_path / "workspaces")
    workspace = runtime.provision_workspace("session-1")

    runtime.clone_repo(str(source_repo), "main", workspace)

    assert (workspace / ".git").exists()
    assert (workspace / "README.md").read_text() == "# Real repo\n"


def _run(command: list[str], cwd: Path) -> None:
    import subprocess

    subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True)
