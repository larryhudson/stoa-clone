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

### Run the dev server

```bash
uv run uvicorn app.main:app --reload
```

## Frontend

The frontend lives under `frontend/` and uses Vite + React + Vitest.

### Install frontend dependencies

```bash
cd frontend
npm install
```

If Node is installed through `nvm`, make sure the active shell has your Node bin directory on `PATH`.

### Run frontend tests

```bash
cd frontend
npm test
```

### Generate frontend API types from OpenAPI

Export the backend schema first:

```bash
uv run python scripts/export_openapi.py
```

Then generate the frontend TypeScript schema:

```bash
cd frontend
npm run api:generate
```

The frontend uses `openapi-typescript` for schema types and `openapi-fetch` for the runtime client.

### Run the frontend dev server

```bash
cd frontend
npm run dev
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

For agent execution, the default app container starts `pi` in RPC mode from the session workspace using:

```text
pi --mode rpc --no-session
```

If `pi` is not on the process `PATH`, set `PI_BIN` to an absolute binary path before starting the app or running tests:

```bash
PI_BIN=/absolute/path/to/pi uv run uvicorn app.main:app --reload
```

Tests generally use in-memory stores and fake runtimes unless a test explicitly targets persistence or real git cloning behavior.
