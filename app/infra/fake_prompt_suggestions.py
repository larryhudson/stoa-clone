from __future__ import annotations

from app.domain.models import PromptSuggestionContext, PromptSuggestionDraft


class FakePromptSuggestionGenerator:
    def suggest(self, context: PromptSuggestionContext) -> list[PromptSuggestionDraft]:
        if not context.transcript:
            return []
        if context.pending_suggestions:
            return []

        latest_message = context.transcript[-1]
        body = latest_message.body.lower()
        if not any(word in body for word in ["add", "build", "implement", "fix", "write"]):
            return []

        return [
            PromptSuggestionDraft(
                text="Add hello world to the README.",
                reason="A meeting message described implementation intent.",
                source_message_ids=[latest_message.id],
            )
        ]
