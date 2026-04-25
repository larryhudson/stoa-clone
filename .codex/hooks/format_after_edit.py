from __future__ import annotations

import difflib
import json
import subprocess
import sys
from pathlib import Path

FRONTEND_EXTENSIONS = {
    ".css",
    ".html",
    ".js",
    ".json",
    ".jsx",
    ".mjs",
    ".ts",
    ".tsx",
}

IGNORED_PARTS = {
    ".git",
    ".ruff_cache",
    ".venv",
    "dist",
    "node_modules",
    "__pycache__",
}


def main() -> int:
    payload = _read_payload()
    cwd = Path(payload.get("cwd") or Path.cwd())
    root = _git_root(cwd)
    changed_files = _changed_files(root)

    python_files = [path for path in changed_files if path.suffix == ".py"]
    frontend_files = [path for path in changed_files if _is_frontend_tool_file(path)]
    tool_files = sorted(set([*python_files, *frontend_files]))
    before_texts = _file_texts(root, tool_files)

    commands: list[tuple[list[str], Path]] = []
    if python_files:
        python_args = [str(path) for path in python_files]
        commands.extend(
            [
                (["uv", "run", "ruff", "check", "--fix", "--", *python_args], root),
                (["uv", "run", "ruff", "format", "--", *python_args], root),
            ]
        )

    if frontend_files:
        commands.append((["npm", "run", "check", "--", "--fix"], root / "frontend"))

    for command, command_cwd in commands:
        completed = subprocess.run(
            command,
            cwd=command_cwd,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            _print_failure(command, completed)
            return 2

    if commands:
        after_texts = _file_texts(root, tool_files)
        _print_context(before_texts, after_texts)

    return 0


def _read_payload() -> dict:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}


def _git_root(cwd: Path) -> Path:
    completed = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=True,
    )
    return Path(completed.stdout.strip())


def _changed_files(root: Path) -> list[Path]:
    tracked = _git_lines(
        root,
        ["git", "diff", "--name-only", "--diff-filter=ACMR", "HEAD", "--"],
    )
    untracked = _git_lines(
        root,
        ["git", "ls-files", "--others", "--exclude-standard"],
    )

    paths = []
    for raw_path in [*tracked, *untracked]:
        path = Path(raw_path)
        if not _is_ignored(path) and (root / path).is_file():
            paths.append(path)
    return sorted(set(paths))


def _git_lines(root: Path, command: list[str]) -> list[str]:
    completed = subprocess.run(
        command,
        cwd=root,
        text=True,
        capture_output=True,
        check=True,
    )
    return [line for line in completed.stdout.splitlines() if line]


def _file_texts(root: Path, paths: list[Path]) -> dict[str, str]:
    texts = {}
    for path in paths:
        absolute_path = root / path
        if absolute_path.is_file():
            texts[str(path)] = absolute_path.read_text(errors="replace")
    return texts


def _is_ignored(path: Path) -> bool:
    return any(part in IGNORED_PARTS for part in path.parts)


def _is_frontend_tool_file(path: Path) -> bool:
    if not path.parts or path.parts[0] != "frontend":
        return False
    if _is_ignored(path):
        return False
    if path.suffix in FRONTEND_EXTENSIONS:
        return True
    return path.name in {"package-lock.json", "package.json", "vite.config.ts"}


def _print_failure(command: list[str], completed: subprocess.CompletedProcess[str]) -> None:
    print("Codex auto-format/lint failed.", file=sys.stderr)
    print(f"Command: {' '.join(command)}", file=sys.stderr)
    if completed.stdout:
        print(completed.stdout, file=sys.stderr)
    if completed.stderr:
        print(completed.stderr, file=sys.stderr)


def _print_context(before_texts: dict[str, str], after_texts: dict[str, str]) -> None:
    diff = _format_diff(before_texts, after_texts)
    if not diff:
        return

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": f"Auto-fix diff:\n{diff}",
                }
            }
        )
    )


def _format_diff(before_texts: dict[str, str], after_texts: dict[str, str]) -> str:
    lines = []
    for path in sorted(after_texts):
        before = before_texts.get(path)
        after = after_texts[path]
        if before == after:
            continue
        lines.append(path)
        lines.extend(
            line
            for line in difflib.unified_diff(
                before.splitlines(),
                after.splitlines(),
                lineterm="",
                n=0,
            )
            if not line.startswith(("--- ", "+++ "))
        )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
