from __future__ import annotations

from pathlib import Path


class FakeAgentRuntime:
    def __init__(self) -> None:
        self.start_calls: list[tuple[str, Path]] = []
        self.prompt_calls: list[tuple[str, str]] = []
        self.steer_calls: list[tuple[str, str]] = []
        self.abort_calls: list[str] = []

    def start_agent_session(self, session_id: str, workspace: Path) -> str:
        self.start_calls.append((session_id, workspace))
        return f"agent-{session_id}"

    def prompt(self, agent_session_id: str, text: str) -> None:
        self.prompt_calls.append((agent_session_id, text))

    def steer(self, agent_session_id: str, text: str) -> None:
        self.steer_calls.append((agent_session_id, text))

    def abort(self, agent_session_id: str) -> None:
        self.abort_calls.append(agent_session_id)
