# stoa-clone

Minimal Python backend shell for a multiplayer agent-session web app.

Inspired by https://withstoa.com/

## Development

This project uses `uv`.

### Install dependencies

```bash
uv sync --dev
```

### Run tests

```bash
uv run pytest -q
```

### Run tests in watch mode

```bash
uv run ptw --config pytest.ini -- -q
```

Run a single test in watch mode:

```bash
uv run ptw --config pytest.ini tests/domain/test_sessions.py::test_can_create_session_for_repo_url -- -q -x
```

## Current TDD workflow

The repo is being built red-green from domain tests outward.

A useful pattern is:

```bash
uv run pytest -q tests/domain/test_sessions.py::test_can_create_session_for_repo_url
```

## Session storage

The default app container uses a JSON-backed session store.

By default, session data is written under the system temp directory in:

```text
<temp>/stoa-clone-workspaces/sessions.json
```

## Runtime

The default app container uses a real git-based runtime for cloning repositories into:

```text
<temp>/stoa-clone-workspaces/<session-id>
```

Tests generally use in-memory stores and fake runtimes unless a test explicitly targets persistence or real git cloning behavior.
