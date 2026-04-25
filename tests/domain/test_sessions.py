from app.domain.models import AgentStatus, SessionStatus
from app.domain.services import SessionService
from app.infra.fake_agent_runtime import FakeAgentRuntime
from app.infra.fake_runtime import FakeRuntime
from app.infra.in_memory import InMemorySessionStore
from app.infra.json_store import JsonSessionStore


def test_can_create_session_for_repo_url(tmp_path):
    service = SessionService(InMemorySessionStore(), FakeRuntime(tmp_path))

    session = service.create_session("https://github.com/example/repo.git", branch="main")

    assert session.repo_url == "https://github.com/example/repo.git"
    assert session.branch == "main"
    assert session.status == SessionStatus.CREATED


def test_starting_session_provisions_workspace_clones_repo_and_starts_agent(tmp_path):
    runtime = FakeRuntime(tmp_path)
    agent_runtime = FakeAgentRuntime()
    service = SessionService(InMemorySessionStore(), runtime, agent_runtime=agent_runtime)
    session = service.create_session("https://github.com/example/repo.git", branch="main")

    started = service.start_session(session.id)

    assert started.status == SessionStatus.READY
    assert started.workspace_path is not None
    assert started.agent_session_id == f"agent-{session.id}"
    assert started.agent_status == AgentStatus.IDLE
    assert runtime.clone_calls == [
        (
            "https://github.com/example/repo.git",
            "main",
            tmp_path / session.id,
        )
    ]
    assert agent_runtime.start_calls == [(session.id, tmp_path / session.id)]


def test_controller_can_submit_prompt_to_running_agent_session(tmp_path):
    runtime = FakeRuntime(tmp_path)
    agent_runtime = FakeAgentRuntime()
    service = SessionService(InMemorySessionStore(), runtime, agent_runtime=agent_runtime)
    session = service.create_session("https://github.com/example/repo.git", branch="main")
    service.start_session(session.id)
    service.claim_control(session.id, "user-1")

    prompted = service.prompt_agent(session.id, "user-1", "Summarize this repository")

    assert prompted.agent_status == AgentStatus.RUNNING
    assert agent_runtime.prompt_calls == [
        (f"agent-{session.id}", "Summarize this repository"),
    ]
    assert prompted.events[-1] == {
        "type": "agent_prompt_submitted",
        "session_id": session.id,
        "user_id": "user-1",
        "text": "Summarize this repository",
    }


def test_prompt_does_not_overwrite_runtime_finished_status(tmp_path):
    store = JsonSessionStore(tmp_path / "sessions.json")
    runtime = FakeRuntime(tmp_path / "workspaces")
    service: SessionService | None = None

    class FinishingAgentRuntime:
        def start_agent_session(self, session_id: str, workspace) -> str:
            return f"agent-{session_id}"

        def prompt(self, agent_session_id: str, text: str) -> None:
            assert service is not None
            session_id = agent_session_id.removeprefix("agent-")
            service.record_runtime_event(
                session_id,
                {"type": "agent_run_finished", "session_id": session_id},
            )

        def steer(self, agent_session_id: str, text: str) -> None:
            return None

        def abort(self, agent_session_id: str) -> None:
            return None

    service = SessionService(store, runtime, agent_runtime=FinishingAgentRuntime())
    session = service.create_session("https://github.com/example/repo.git", branch="main")
    service.start_session(session.id)
    service.claim_control(session.id, "user-1")

    prompted = service.prompt_agent(session.id, "user-1", "Summarize this repository")

    assert prompted.agent_status == AgentStatus.IDLE
    assert store.get(session.id).agent_status == AgentStatus.IDLE
    assert prompted.events[-2:] == [
        {
            "type": "agent_prompt_submitted",
            "session_id": session.id,
            "user_id": "user-1",
            "text": "Summarize this repository",
        },
        {"type": "agent_run_finished", "session_id": session.id},
    ]



def test_controller_can_steer_and_abort_running_agent_session(tmp_path):
    runtime = FakeRuntime(tmp_path)
    agent_runtime = FakeAgentRuntime()
    service = SessionService(InMemorySessionStore(), runtime, agent_runtime=agent_runtime)
    session = service.create_session("https://github.com/example/repo.git", branch="main")
    service.start_session(session.id)
    service.claim_control(session.id, "user-1")
    service.prompt_agent(session.id, "user-1", "Initial instruction")

    steered = service.steer_agent(session.id, "user-1", "Focus on tests")

    assert steered.agent_status == AgentStatus.RUNNING
    assert agent_runtime.steer_calls == [
        (f"agent-{session.id}", "Focus on tests"),
    ]
    assert steered.events[-1] == {
        "type": "agent_steered",
        "session_id": session.id,
        "user_id": "user-1",
        "text": "Focus on tests",
    }

    aborted = service.abort_agent(session.id, "user-1")

    assert agent_runtime.abort_calls == [f"agent-{session.id}"]
    assert aborted.agent_status == AgentStatus.RUNNING
    assert aborted.events[-1] == {
        "type": "agent_aborted",
        "session_id": session.id,
        "user_id": "user-1",
    }
