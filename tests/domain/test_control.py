import pytest

from app.domain.services import SessionService
from app.infra.fake_runtime import FakeRuntime
from app.infra.in_memory import InMemorySessionStore


def test_only_one_viewer_can_hold_control_at_a_time(tmp_path):
    service = SessionService(InMemorySessionStore(), FakeRuntime(tmp_path))
    session = service.create_session("https://github.com/example/repo.git")

    claimed = service.claim_control(session.id, "user-1")

    assert claimed.controller_id == "user-1"
    with pytest.raises(ValueError, match="control already held"):
        service.claim_control(session.id, "user-2")


def test_controller_can_release_control(tmp_path):
    service = SessionService(InMemorySessionStore(), FakeRuntime(tmp_path))
    session = service.create_session("https://github.com/example/repo.git")
    service.claim_control(session.id, "user-1")

    released = service.release_control(session.id, "user-1")

    assert released.controller_id is None
