import pytest

from app.domain.events import FileEdited


def test_controller_edit_updates_file_and_publishes_event(
    tmp_path,
    session_service,
    file_editing_service,
    event_publisher,
):
    session = session_service.create_session("https://github.com/example/repo.git")
    session_service.start_session(session.id)
    session_service.claim_control(session.id, "user-1")
    event_publisher.published.clear()

    file_editing_service.edit_file(
        session_id=session.id,
        user_id="user-1",
        path="README.md",
        new_content="# Updated\n",
    )

    assert (tmp_path / session.id / "README.md").read_text() == "# Updated\n"
    assert event_publisher.published == [
        FileEdited(
            session_id=session.id,
            path="README.md",
            editor_id="user-1",
            content="# Updated\n",
        )
    ]


def test_non_controller_cannot_edit_file_or_publish_event(
    tmp_path,
    session_service,
    file_editing_service,
    event_publisher,
):
    session = session_service.create_session("https://github.com/example/repo.git")
    session_service.start_session(session.id)
    session_service.claim_control(session.id, "user-1")
    event_publisher.published.clear()
    original_content = (tmp_path / session.id / "README.md").read_text()

    with pytest.raises(PermissionError) as exc_info:
        file_editing_service.edit_file(
            session_id=session.id,
            user_id="user-2",
            path="README.md",
            new_content="# Unauthorized\n",
        )

    assert str(exc_info.value) == "only controller can edit files"

    assert (tmp_path / session.id / "README.md").read_text() == original_content
    assert event_publisher.published == []
