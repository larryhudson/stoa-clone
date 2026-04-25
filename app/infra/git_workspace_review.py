from __future__ import annotations

import subprocess
from pathlib import Path

from app.domain.models import Session, WorkspaceSummary
from app.domain.services import is_hidden_path


class GitWorkspaceReviewProvider:
    def get_summary(self, session: Session) -> WorkspaceSummary:
        if not session.workspace_path:
            raise ValueError("session has no workspace")

        workspace = Path(session.workspace_path)
        changed_files = self._changed_files(workspace)
        visible_files = [path for path in changed_files if not is_hidden_path(Path(path))]
        return WorkspaceSummary(
            changed_files=visible_files,
            diff=self._diff(workspace, visible_files),
        )

    def _changed_files(self, workspace: Path) -> list[str]:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=workspace,
            check=True,
            capture_output=True,
            text=True,
        )
        paths = []
        for line in result.stdout.splitlines():
            path = line[3:]
            if " -> " in path:
                path = path.split(" -> ", maxsplit=1)[1]
            paths.append(path)
        return sorted(paths)

    def _diff(self, workspace: Path, visible_files: list[str]) -> str:
        if not visible_files:
            return ""
        result = subprocess.run(
            ["git", "diff", "--no-ext-diff", "--", *visible_files],
            cwd=workspace,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout
