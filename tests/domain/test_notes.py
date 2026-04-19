from app.domain.services import SessionService
from app.infra.fake_runtime import FakeRuntime
from app.infra.in_memory import InMemorySessionStore


def test_any_viewer_can_add_notes(tmp_path):
    service = SessionService(InMemorySessionStore(), FakeRuntime(tmp_path))
    session = service.create_session("https://github.com/example/repo.git")

    first = service.add_note(session.id, "user-1", "watching this")
    second = service.add_note(session.id, "user-2", "looks good")

    assert first.created_at < second.created_at
    assert session.notes == [first, second]
