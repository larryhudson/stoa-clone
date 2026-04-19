import pytest

from app.domain.services import FileEditingService, FileService, SessionService
from app.infra.in_memory import InMemorySessionStore


class StubEventPublisher:
    def publish(self, event: object) -> None:
        return None


class HiddenPathsRuntime:
    def __init__(self, base_dir):
        self.base_dir = base_dir

    def provision_workspace(self, session_id: str):
        workspace = self.base_dir / session_id
        workspace.mkdir(parents=True, exist_ok=True)
        return workspace

    def clone_repo(self, repo_url: str, branch: str, workspace):
        (workspace / "README.md").write_text("# Visible\n")
        (workspace / ".git").mkdir()
        (workspace / ".git" / "HEAD").write_text("ref: refs/heads/main\n")
        (workspace / "node_modules").mkdir()
        (workspace / "node_modules" / "package.json").write_text("{}\n")


def test_hidden_paths_are_excluded_from_listing_and_direct_access(tmp_path):
    store = InMemorySessionStore()
    runtime = HiddenPathsRuntime(tmp_path)
    session_service = SessionService(store, runtime)
    file_service = FileService(store)
    session = session_service.create_session("ignored")
    session_service.start_session(session.id)

    files = file_service.list_files(session.id)

    assert files == ["README.md"]
    with pytest.raises(ValueError, match="path is hidden"):
        file_service.read_file(session.id, ".git/HEAD")
    with pytest.raises(ValueError, match="path is hidden"):
        file_service.render_preview(session.id, "node_modules/package.json")


def test_hidden_paths_cannot_be_edited(tmp_path):
    store = InMemorySessionStore()
    runtime = HiddenPathsRuntime(tmp_path)
    session_service = SessionService(store, runtime)
    file_editing_service = FileEditingService(store, StubEventPublisher())
    session = session_service.create_session("ignored")
    session_service.start_session(session.id)
    session_service.claim_control(session.id, "user-1")

    with pytest.raises(ValueError, match="path is hidden"):
        file_editing_service.edit_file(
            session_id=session.id,
            user_id="user-1",
            path=".git/HEAD",
            new_content="nope\n",
        )
