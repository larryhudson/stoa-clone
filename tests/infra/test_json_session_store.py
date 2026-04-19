from app.domain.models import Note, Session, SessionStatus
from app.infra.json_store import JsonSessionStore


def test_json_session_store_persists_sessions_to_disk(tmp_path):
    store_path = tmp_path / "sessions.json"
    store = JsonSessionStore(store_path)
    session = Session(
        id="session-1",
        repo_url="https://github.com/example/repo.git",
        branch="main",
        status=SessionStatus.READY,
        workspace_path="/tmp/workspace",
        viewers={"user-1", "user-2"},
        controller_id="user-1",
        notes=[Note(author_id="user-2", body="watching", created_at=1)],
    )

    store.add(session)

    reloaded = JsonSessionStore(store_path).get("session-1")
    assert reloaded == session
