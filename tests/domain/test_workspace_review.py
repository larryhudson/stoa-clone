from app.infra.git_workspace_review import GitWorkspaceReviewProvider

from app.domain.models import WorkspaceSummary
from app.domain.services import WorkspaceReviewService
from app.infra.in_memory import InMemorySessionStore


def test_workspace_review_reports_changed_files_and_git_diff(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _run(["git", "init", "-b", "main"], workspace)
    (workspace / "README.md").write_text("# Before\n")
    _run(["git", "add", "README.md"], workspace)
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
        workspace,
    )
    (workspace / "README.md").write_text("# After\n")

    store = InMemorySessionStore()
    session = _session_with_workspace(store, str(workspace))
    service = WorkspaceReviewService(store, GitWorkspaceReviewProvider())

    assert service.get_review(session.id) == WorkspaceSummary(
        changed_files=["README.md"],
        diff=_git_diff(workspace),
    )


def test_workspace_review_hides_protected_paths(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _run(["git", "init", "-b", "main"], workspace)
    (workspace / "README.md").write_text("# Before\n")
    _run(["git", "add", "README.md"], workspace)
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
        workspace,
    )
    (workspace / "node_modules").mkdir()
    (workspace / "node_modules" / "hidden.js").write_text("hidden")

    store = InMemorySessionStore()
    session = _session_with_workspace(store, str(workspace))
    service = WorkspaceReviewService(store, GitWorkspaceReviewProvider())

    assert service.get_review(session.id) == WorkspaceSummary(changed_files=[], diff="")


def _session_with_workspace(store, workspace_path):
    from app.domain.models import Session, SessionStatus

    session = Session(
        id="session-1",
        repo_url="https://github.com/example/repo.git",
        status=SessionStatus.READY,
        workspace_path=workspace_path,
    )
    store.add(session)
    return session


def _git_diff(workspace):
    import subprocess

    return subprocess.run(
        ["git", "diff", "--no-ext-diff"],
        cwd=workspace,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def _run(command, cwd):
    import subprocess

    subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True)
