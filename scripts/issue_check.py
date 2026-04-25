#!/usr/bin/env python3
"""Run a check command quietly unless it reports issues."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from xml.etree import ElementTree


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a command and print output only if it fails.")
    parser.add_argument(
        "--renderer",
        choices=("output", "pytest-junit", "vitest-json"),
        default="output",
        help="How to render failing command output",
    )
    parser.add_argument("label", help="Short human-readable check name")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Command after --")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        print("issue_check.py: missing command", file=sys.stderr)
        return 2

    display_command = command.copy()
    report_path: Path | None = None
    if args.renderer != "output":
        report = tempfile.NamedTemporaryFile(delete=False)
        report_path = Path(report.name)
        report.close()
        command = command_with_report(command, args.renderer, report_path)

    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode == 0:
        print(f"✓ {args.label}")
        if report_path:
            report_path.unlink(missing_ok=True)
        return 0

    print(f"✗ {args.label}")
    print(f"$ {shlex.join(display_command)}")
    output = render_issues(command, result.stdout + result.stderr, args.renderer, report_path)
    if report_path:
        report_path.unlink(missing_ok=True)
    if output:
        print(output, end="" if output.endswith("\n") else "\n")
    return result.returncode


def command_with_report(command: list[str], renderer: str, report_path: Path) -> list[str]:
    if renderer == "pytest-junit":
        return [*command, f"--junit-xml={report_path}"]
    if renderer == "vitest-json":
        return [*command, "--reporter=json", f"--outputFile={report_path}"]
    return command


def render_issues(command: list[str], output: str, renderer: str, report_path: Path | None) -> str:
    if renderer == "pytest-junit" and report_path:
        rendered = render_pytest_junit(report_path)
        return rendered or output
    if renderer == "vitest-json" and report_path:
        rendered = render_vitest_json(report_path)
        return rendered or output
    return output


def render_pytest_junit(report_path: Path) -> str:
    if not report_path.exists() or report_path.stat().st_size == 0:
        return ""

    root = ElementTree.parse(report_path).getroot()
    issues = []
    for case in root.iter("testcase"):
        failure = case.find("failure")
        error = case.find("error")
        node = failure if failure is not None else error
        if node is None:
            continue
        name = f"{case.attrib.get('classname', '')}.{case.attrib.get('name', '')}".strip(".")
        body = (node.text or node.attrib.get("message") or "").strip()
        issues.append(format_issue(name, body))
    return "\n\n".join(issues) + ("\n" if issues else "")


def render_vitest_json(report_path: Path) -> str:
    if not report_path.exists() or report_path.stat().st_size == 0:
        return ""

    data = json.loads(report_path.read_text())
    issues = []
    for suite in data.get("testResults", []):
        if suite.get("status") != "failed":
            continue
        suite_name = relativize_path(suite.get("name", ""))
        for assertion in suite.get("assertionResults", []):
            if assertion.get("status") != "failed":
                continue
            title = assertion.get("fullName") or assertion.get("title") or "failed test"
            messages = "\n".join(assertion.get("failureMessages", []))
            issues.append(format_issue(f"{suite_name} > {title}", clean_vitest_message(messages)))
    return "\n\n".join(issues) + ("\n" if issues else "")


def clean_vitest_message(message: str) -> str:
    lines = []
    for line in message.splitlines():
        stripped = line.strip()
        if "node_modules" in stripped:
            continue
        if stripped == "at new Promise (<anonymous>)":
            continue
        lines.append(relativize_path(line))
    return "\n".join(lines).strip()


def format_issue(name: str, body: str) -> str:
    return f"FAILED {name}\n{body}".rstrip()


def relativize_path(text: str) -> str:
    cwd = str(Path.cwd()) + "/"
    return text.replace(cwd, "")


if __name__ == "__main__":
    raise SystemExit(main())
