import time
from threading import Timer

from app.domain.models import AgentOutputStatus, AgentStatus
from app.domain.services import SessionService
from app.infra.fake_agent_runtime import FakeAgentRuntime
from app.infra.fake_runtime import FakeRuntime
from app.infra.in_memory import InMemorySessionStore



def test_runtime_events_are_recorded_and_update_agent_status(tmp_path):
    store = InMemorySessionStore()
    service = SessionService(store, FakeRuntime(tmp_path), agent_runtime=FakeAgentRuntime())
    session = service.create_session("https://github.com/example/repo.git")
    service.start_session(session.id)

    service.record_runtime_event(session.id, {"type": "agent_run_started", "session_id": session.id})
    service.record_runtime_event(
        session.id,
        {"type": "agent_text_delta", "session_id": session.id, "delta": "Hello"},
    )
    updated = service.record_runtime_event(
        session.id,
        {"type": "agent_run_finished", "session_id": session.id},
    )

    assert updated.agent_status == AgentStatus.IDLE
    assert updated.agent_output == "Hello"
    assert updated.agent_output_status == AgentOutputStatus.COMPLETE
    assert updated.agent_output_error is None
    assert updated.events[-3:] == [
        {"type": "agent_run_started", "session_id": session.id},
        {"type": "agent_text_delta", "session_id": session.id, "delta": "Hello"},
        {"type": "agent_run_finished", "session_id": session.id},
    ]


def test_prompt_resets_agent_output_before_next_run(tmp_path):
    store = InMemorySessionStore()
    service = SessionService(store, FakeRuntime(tmp_path), agent_runtime=FakeAgentRuntime())
    session = service.create_session("https://github.com/example/repo.git")
    service.start_session(session.id)
    service.claim_control(session.id, "user-1")

    service.record_runtime_event(
        session.id,
        {"type": "agent_text_delta", "session_id": session.id, "delta": "Old output"},
    )

    prompted = service.prompt_agent(session.id, "user-1", "Summarize this repository")

    assert prompted.agent_output == ""
    assert prompted.agent_output_status == AgentOutputStatus.PENDING
    assert prompted.agent_output_error is None


def test_failed_runtime_event_marks_output_failed_and_keeps_error(tmp_path):
    store = InMemorySessionStore()
    service = SessionService(store, FakeRuntime(tmp_path), agent_runtime=FakeAgentRuntime())
    session = service.create_session("https://github.com/example/repo.git")
    service.start_session(session.id)

    updated = service.record_runtime_event(
        session.id,
        {
            "type": "agent_run_failed",
            "session_id": session.id,
            "error": "No API key found",
        },
    )

    assert updated.agent_status == AgentStatus.FAILED
    assert updated.agent_output_status == AgentOutputStatus.FAILED
    assert updated.agent_output_error == "No API key found"
