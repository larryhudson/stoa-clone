from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class GitRuntime:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir

    def provision_workspace(self, session_id: str) -> Path:
        workspace = self.base_dir / session_id
        workspace.mkdir(parents=True, exist_ok=True)
        return workspace

    def clone_repo(self, repo_url: str, branch: str, workspace: Path) -> None:
        git = shutil.which("git")
        if git is None:
            raise RuntimeError("git executable not found")

        subprocess.run(
            [
                git,
                "clone",
                "--branch",
                branch,
                "--single-branch",
                repo_url,
                str(workspace),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
