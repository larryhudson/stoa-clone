import time
from threading import Timer

from app.domain.models import AgentStatus
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
    assert updated.events[-3:] == [
        {"type": "agent_run_started", "session_id": session.id},
        {"type": "agent_text_delta", "session_id": session.id, "delta": "Hello"},
        {"type": "agent_run_finished", "session_id": session.id},
    ]
