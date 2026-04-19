from app.domain.services import FileService, SessionService
from app.infra.fake_runtime import FakeRuntime
from app.infra.in_memory import InMemorySessionStore


def test_files_in_workspace_can_be_listed_read_and_previewed(tmp_path):
    store = InMemorySessionStore()
    runtime = FakeRuntime(tmp_path)
    session_service = SessionService(store, runtime)
    file_service = FileService(store)
    session = session_service.create_session("https://github.com/example/repo.git")
    session_service.start_session(session.id)

    files = file_service.list_files(session.id)
    content = file_service.read_file(session.id, "README.md")
    html = file_service.render_preview(session.id, "README.md")

    assert ".repo-origin" in files
    assert "README.md" in files
    assert "# Cloned repo" in content
    assert "<h1>Cloned repo</h1>" in html
