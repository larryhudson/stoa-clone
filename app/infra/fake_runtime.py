from __future__ import annotations

import subprocess
from pathlib import Path


class FakeRuntime:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.clone_calls: list[tuple[str, str, Path]] = []

    def provision_workspace(self, session_id: str) -> Path:
        workspace = self.base_dir / session_id
        workspace.mkdir(parents=True, exist_ok=True)
        return workspace

    def clone_repo(self, repo_url: str, branch: str, workspace: Path) -> None:
        self.clone_calls.append((repo_url, branch, workspace))
        (workspace / ".repo-origin").write_text(f"{repo_url}@{branch}\n")
        (workspace / "README.md").write_text("# Cloned repo\n\nThis came from the fake runtime.\n")
        subprocess.run(
            ["git", "init", "-b", branch],
            cwd=workspace,
            check=True,
            capture_output=True,
        )
        subprocess.run(["git", "add", "."], cwd=workspace, check=True, capture_output=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Test User",
                "-c",
                "user.email=test@example.com",
                "commit",
                "-m",
                "initial",
            ],
            cwd=workspace,
            check=True,
            capture_output=True,
        )
