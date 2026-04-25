from app.domain.models import PromptSuggestionDraft, WorkspaceSummary


class RecordingSuggestionGenerator:
    def __init__(self) -> None:
        self.contexts = []

    def suggest(self, context):
        self.contexts.append(context)
        return [
            PromptSuggestionDraft(
                text="Inspect the repo and write failing tests for session chat.",
                reason="The meeting discussed a concrete product slice.",
                source_message_ids=[context.transcript[-1].id],
            )
        ]


class StaticWorkspaceSummaryProvider:
    def get_summary(self, session):
        return WorkspaceSummary(
            changed_files=["README.md"],
            diff="diff --git a/README.md b/README.md",
        )


def test_posting_chat_invokes_suggestion_generator_with_meeting_agent_and_workspace_context(
    session_service,
):
    generator = RecordingSuggestionGenerator()
    session_service.prompt_suggestion_generator = generator
    session_service.workspace_summary_provider = StaticWorkspaceSummaryProvider()
    session = session_service.create_session("https://github.com/example/repo.git")
    session_service.start_session(session.id)
    session_service.join_session(session.id, "user-1")

    message = session_service.post_chat_message(session.id, "user-1", "Let's add meeting chat.")

    assert len(generator.contexts) == 1
    context = generator.contexts[0]
    assert context.transcript == [message]
    assert context.agent_status == session.agent_status
    assert context.recent_agent_events == session.events[-5:-1]
    assert context.workspace_summary == WorkspaceSummary(
        changed_files=["README.md"],
        diff="diff --git a/README.md b/README.md",
    )


def test_generated_suggestions_are_stored_as_pending_suggestions(session_service):
    generator = RecordingSuggestionGenerator()
    session_service.prompt_suggestion_generator = generator
    session = session_service.create_session("https://github.com/example/repo.git")
    session_service.start_session(session.id)
    session_service.join_session(session.id, "user-1")

    message = session_service.post_chat_message(session.id, "user-1", "Let's add meeting chat.")

    suggestion = session.prompt_suggestions[0]
    assert suggestion.text == "Inspect the repo and write failing tests for session chat."
    assert suggestion.reason == "The meeting discussed a concrete product slice."
    assert suggestion.source_message_ids == [message.id]
    assert suggestion.status == "pending"


def test_non_controller_cannot_accept_or_dismiss_suggestions(session_service):
    generator = RecordingSuggestionGenerator()
    session_service.prompt_suggestion_generator = generator
    session = session_service.create_session("https://github.com/example/repo.git")
    session_service.start_session(session.id)
    session_service.join_session(session.id, "user-1")
    session_service.post_chat_message(session.id, "user-1", "Let's add meeting chat.")
    suggestion = session.prompt_suggestions[0]

    for action in [
        lambda: session_service.accept_prompt_suggestion(session.id, "user-1", suggestion.id),
        lambda: session_service.dismiss_prompt_suggestion(session.id, "user-1", suggestion.id),
    ]:
        try:
            action()
        except PermissionError as exc:
            assert str(exc) == "only controller can manage prompt suggestions"
        else:
            raise AssertionError("expected suggestion action to require control")


def test_controller_accepting_suggestion_prompts_agent_and_marks_it_accepted(
    session_service,
    agent_runtime,
):
    generator = RecordingSuggestionGenerator()
    session_service.prompt_suggestion_generator = generator
    session = session_service.create_session("https://github.com/example/repo.git")
    session_service.start_session(session.id)
    session_service.join_session(session.id, "user-1")
    session_service.claim_control(session.id, "user-1")
    session_service.post_chat_message(session.id, "user-1", "Let's add meeting chat.")
    suggestion = session.prompt_suggestions[0]

    updated = session_service.accept_prompt_suggestion(session.id, "user-1", suggestion.id)

    assert updated.prompt_suggestions[0].status == "accepted"
    assert agent_runtime.prompt_calls == [
        (session.agent_session_id, "Inspect the repo and write failing tests for session chat.")
    ]


def test_controller_dismissing_suggestion_marks_it_dismissed_without_prompting_agent(
    session_service,
    agent_runtime,
):
    generator = RecordingSuggestionGenerator()
    session_service.prompt_suggestion_generator = generator
    session = session_service.create_session("https://github.com/example/repo.git")
    session_service.start_session(session.id)
    session_service.join_session(session.id, "user-1")
    session_service.claim_control(session.id, "user-1")
    session_service.post_chat_message(session.id, "user-1", "Let's add meeting chat.")
    suggestion = session.prompt_suggestions[0]

    updated = session_service.dismiss_prompt_suggestion(session.id, "user-1", suggestion.id)

    assert updated.prompt_suggestions[0].status == "dismissed"
    assert agent_runtime.prompt_calls == []
