import pytest

from app.domain.models import SessionStatus
from app.domain.services import SessionService
from app.infra.in_memory import InMemorySessionStore
from app.infra.pi_rpc_agent_runtime import PiRpcAgentRuntime


class FailingRuntime:
    def provision_workspace(self, session_id: str):
        raise RuntimeError("clone failed")

    def clone_repo(self, repo_url: str, branch: str, workspace):
        raise AssertionError("should not be called")


class FailingAgentRuntime:
    def start_agent_session(self, session_id: str, workspace):
        raise RuntimeError("agent failed")

    def prompt(self, agent_session_id: str, text: str) -> None:
        return None

    def steer(self, agent_session_id: str, text: str) -> None:
        return None

    def abort(self, agent_session_id: str) -> None:
        return None


def test_start_session_marks_session_failed_when_runtime_errors():
    store = InMemorySessionStore()
    service = SessionService(store, FailingRuntime())
    session = service.create_session("https://github.com/example/repo.git")

    with pytest.raises(RuntimeError) as exc_info:
        service.start_session(session.id)

    assert str(exc_info.value) == "clone failed"

    failed = store.get(session.id)
    assert failed.status == SessionStatus.FAILED


def test_start_session_marks_session_failed_when_agent_runtime_errors(tmp_path):
    store = InMemorySessionStore()

    class SuccessfulRuntime:
        def provision_workspace(self, session_id: str):
            workspace = tmp_path / session_id
            workspace.mkdir(parents=True, exist_ok=True)
            return workspace

        def clone_repo(self, repo_url: str, branch: str, workspace):
            (workspace / "README.md").write_text("# Repo\n")

    service = SessionService(
        store,
        SuccessfulRuntime(),
        agent_runtime=FailingAgentRuntime(),
    )
    session = service.create_session("https://github.com/example/repo.git")

    with pytest.raises(RuntimeError) as exc_info:
        service.start_session(session.id)

    assert str(exc_info.value) == "agent failed"

    failed = store.get(session.id)
    assert failed.status == SessionStatus.FAILED


def test_start_session_marks_session_failed_when_agent_process_exits_immediately(tmp_path):
    import sys

    store = InMemorySessionStore()

    class SuccessfulRuntime:
        def provision_workspace(self, session_id: str):
            workspace = tmp_path / session_id
            workspace.mkdir(parents=True, exist_ok=True)
            return workspace

        def clone_repo(self, repo_url: str, branch: str, workspace):
            (workspace / "README.md").write_text("# Repo\n")

    service = SessionService(
        store,
        SuccessfulRuntime(),
        agent_runtime=PiRpcAgentRuntime(command=[sys.executable, "-c", "raise SystemExit(1)"]),
    )
    session = service.create_session("https://github.com/example/repo.git")

    with pytest.raises(RuntimeError) as exc_info:
        service.start_session(session.id)

    assert str(exc_info.value) == "agent session failed to start"

    failed = store.get(session.id)
    assert failed.status == SessionStatus.FAILED
