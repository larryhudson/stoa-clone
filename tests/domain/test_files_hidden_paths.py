from app.domain.services import FileService, SessionService
from app.infra.git_runtime import GitRuntime
from app.infra.in_memory import InMemorySessionStore


def test_file_listing_excludes_git_directory(tmp_path):
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

    store = InMemorySessionStore()
    runtime = GitRuntime(tmp_path / "workspaces")
    session_service = SessionService(store, runtime)
    file_service = FileService(store)
    session = session_service.create_session(str(source_repo), branch="main")
    session_service.start_session(session.id)

    files = file_service.list_files(session.id)

    assert "README.md" in files
    assert all(not path.startswith(".git/") for path in files)
    assert ".git/HEAD" not in files


def _run(command: list[str], cwd):
    import subprocess

    subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True)
