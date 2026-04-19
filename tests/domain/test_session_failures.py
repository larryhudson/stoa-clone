from app.domain.models import SessionStatus
from app.domain.services import SessionService
from app.infra.in_memory import InMemorySessionStore


class FailingRuntime:
    def provision_workspace(self, session_id: str):
        raise RuntimeError("clone failed")

    def clone_repo(self, repo_url: str, branch: str, workspace):
        raise AssertionError("should not be called")


def test_start_session_marks_session_failed_when_runtime_errors():
    store = InMemorySessionStore()
    service = SessionService(store, FailingRuntime())
    session = service.create_session("https://github.com/example/repo.git")

    try:
        service.start_session(session.id)
        assert False, "expected RuntimeError"
    except RuntimeError as exc:
        assert str(exc) == "clone failed"

    failed = store.get(session.id)
    assert failed.status == SessionStatus.FAILED
