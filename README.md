# multiplayer-agent

A small full-stack shell for a multiplayer agent-session app.

The app can create a session for a Git repository, provision a workspace, start a `pi` RPC agent,
join users into the session, stream typed session events over WebSocket, and drive the agent from
the browser.

Inspired by https://withstoa.com/

## Quick Start

Install backend dependencies:

```bash
uv sync --dev
```

Install frontend dependencies:

```bash
cd frontend
vp install
```

Run the full local app:

```bash
make dev
```

`make dev` uses Hivemind and `Procfile.dev` to run:

- backend: http://127.0.0.1:8000
- frontend: http://127.0.0.1:5173

If Hivemind is missing:

```bash
brew install hivemind
```

Open the frontend, enter a repository URL and branch, then create a session. A session can also be
opened directly with:

```text
http://127.0.0.1:5173/?sessionId=<session-id>&userId=user-1
```

## Runtime Requirements

The default app container uses:

- a JSON-backed session store
- a git-based runtime for cloning repositories
- `pi` in RPC mode for agent execution

For agent execution, `pi` must be available on `PATH`:

```text
pi --mode rpc --no-session
```

If needed, point the backend at an explicit binary:

```bash
PI_BIN=/absolute/path/to/pi make dev
```

Without `pi`, session creation and workspace provisioning can still be exercised, but prompting the
agent will fail.

## Verification

Run the full verification sweep:

```bash
make check
```

`make check` runs each command through `scripts/issue_check.py`. Passing commands only print a
checkmarked label; failing commands print the command and rendered issue output. Backend tests are
rendered from pytest JUnit XML; frontend tests are rendered from Vitest JSON.

`make check` runs:

- backend tests
- Ruff lint and format checks
- ty type checks
- frontend tests
- Vite+ checks
- frontend production build

For narrower loops:

```bash
make check-backend
make check-frontend
```

## Backend

The backend is a FastAPI app under `app/`.

Useful commands:

```bash
uv run pytest -q
uv run ruff check .
uv run ruff format .
uv run ty check
```

The default session store writes data under the system temp directory:

```text
<temp>/multiplayer-agent-workspaces/sessions.json
```

Workspaces are cloned into:

```text
<temp>/multiplayer-agent-workspaces/<session-id>
```

Tests generally use in-memory stores and fake runtimes unless a test explicitly targets persistence
or real git cloning behavior.

## Frontend

The frontend lives under `frontend/` and uses:

- React
- Vite+
- TanStack Query
- Testing Library
- OpenAPI-generated HTTP types
- JSON Schema-generated WebSocket event types

Useful commands:

```bash
cd frontend
vp test
vp check
vp build
vp dev
```

## Generated Types

HTTP client types are generated from OpenAPI.

Export the backend OpenAPI schema:

```bash
uv run python scripts/export_openapi.py
```

Generate the frontend TypeScript schema:

```bash
cd frontend
vp run api:generate
```

WebSocket session event types are generated from a backend-owned Pydantic discriminated union.

Export the event JSON Schema:

```bash
uv run python scripts/export_session_events_schema.py
```

Generate the frontend event union:

```bash
cd frontend
vp run events:generate
```

## Pre-Commit

This project uses `prek`:

```bash
uv run prek install
uv run prek run --all-files
```

## Development Approach

The repo is developed in small red-green-refactor slices.

Prefer focused tests close to the behavior being changed:

- domain/service tests for business rules
- API tests for HTTP/WebSocket behavior
- reducer and component tests for frontend state and interaction
- browser smoke tests only for key end-to-end flows
