from app.domain.models import SessionStatus
from app.domain.services import SessionService
from app.infra.fake_runtime import FakeRuntime
from app.infra.in_memory import InMemorySessionStore


def test_can_create_session_for_repo_url(tmp_path):
    service = SessionService(InMemorySessionStore(), FakeRuntime(tmp_path))

    session = service.create_session("https://github.com/example/repo.git", branch="main")

    assert session.repo_url == "https://github.com/example/repo.git"
    assert session.branch == "main"
    assert session.status == SessionStatus.CREATED


def test_starting_session_provisions_workspace_and_clones_repo(tmp_path):
    runtime = FakeRuntime(tmp_path)
    service = SessionService(InMemorySessionStore(), runtime)
    session = service.create_session("https://github.com/example/repo.git", branch="main")

    started = service.start_session(session.id)

    assert started.status == SessionStatus.READY
    assert started.workspace_path is not None
    assert runtime.clone_calls == [
        (
            "https://github.com/example/repo.git",
            "main",
            tmp_path / session.id,
        )
    ]
