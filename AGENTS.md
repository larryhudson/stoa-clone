# AGENTS.md

## Purpose

This repository is being built as a small, incremental backend shell for a multiplayer agent-session app.

This file is only for:
- architectural intent
- development methodology
- repo-wide design principles

Do not treat this file as a source of truth for detailed module/file layout. Explore the code directly.

---

## Architecture principles

### Keep core rules in plain Python
Business rules belong in domain/application services, not in FastAPI routes or infrastructure code.

Examples of domain concerns:
- session lifecycle
- control ownership
- notes
- hidden-path policy
- presence transitions
- event emission

### Ports and adapters
The domain defines the external capabilities it needs.
Infrastructure implements them.

Use ports to keep domain logic independent from:
- storage details
- git/runtime details
- websocket transport details

### Constructor injection + composition root
Dependencies should be passed explicitly into services.
Concrete implementations should be wired in one place at app startup.

Avoid hidden globals.

### HTTP for current state, WebSocket for live updates
Preferred split:
- HTTP endpoints return current state / read models
- WebSocket streams future events

Do not push snapshot/state-fetch responsibilities into the websocket protocol unless a test or requirement clearly calls for it.

### Frontend consumes snapshots plus events
The frontend should initialize from HTTP read models, then apply websocket events incrementally.

Keep the client model aligned with the server read model:
- fetch current session state first
- subscribe to future events second
- on reconnect, refresh from HTTP before trusting new live events

Do not make the UI reconstruct core state entirely from websocket history when the server already exposes a read model.

### Domain knows events, not websockets
The domain may publish typed events.
It should not know about websocket connections or transport concerns.

Websocket broadcasting belongs in infrastructure / API layers.

### Frontend reducer scope should stay narrow
The frontend may use reducers where the UI is consuming server-driven event streams.

In this repo, reducers are a good fit for:
- session state derived from API snapshots plus websocket events
- agent output/status transitions driven by typed runtime events

Do not force reducer patterns onto purely local UI concerns like form inputs, panel visibility, or temporary selection state. Prefer simple local state for those.

---

## Event model

Use typed events for meaningful state changes.
Each event should carry its own event type.

When appropriate, a domain action should:
1. change state
2. record event history
3. publish the typed event for live subscribers

Keep event behavior consistent across:
- domain logic
- stored event history
- websocket live updates

---

## Development methodology

### Red-green-refactor
Work in small requirement-driven loops:
1. write a failing test
2. run it and confirm the red failure
3. implement the minimum code to make it pass
4. refactor while keeping tests green

Do not skip the red step when adding behavior.

### Prefer small vertical slices
Good slices are things like:
- one domain rule
- one API endpoint
- one websocket event
- one failure path

Avoid large speculative rewrites.

### Test pyramid
Bias toward:
1. domain/service tests
2. API tests
3. focused infrastructure tests

Avoid heavy end-to-end UI testing unless explicitly needed.

For frontend work, use a similar pyramid:
1. reducer/view-model tests
2. component rendering/interaction tests
3. a small number of browser integration tests

Do not make full browser automation the default red-green loop for ordinary UI behavior.

### Frontend stack
The frontend uses:
- React
- Vite
- Vitest
- Testing Library

Keep frontend code and tooling under `frontend/`.

### Frontend TDD workflow
For UI work, prefer:
1. failing reducer/view-model test for event/state behavior
2. minimal implementation
3. failing component test for rendering/interaction behavior
4. minimal implementation
5. broader browser-level coverage only for key end-to-end flows

Examples of behavior that should usually start with reducer/view-model tests:
- websocket event application
- agent output/status transitions
- control gating
- reconnect/snapshot merge behavior

### Use fixtures, but keep tests readable
Prefer pytest fixtures for reusable setup.
If setup needs variation, prefer fixture factories over a growing list of one-off fixtures.

Do not hide the main behavior under test behind too much fixture indirection.

---

## Design preferences

### Keep routes thin
Routes should mainly:
- parse input
- call services
- map errors/results to transport responses

If logic feels important to product behavior, it probably belongs in a service.

### Separate queries from commands where useful
Read behavior and state-changing behavior often evolve differently.
Keep them separate when that improves clarity.

The same applies in the frontend:
- server snapshots/read models should be treated as query state
- prompt/steer/abort/claim actions should be treated as commands
- live websocket events should update query state, not replace command handling

### Be explicit about failure paths
Failure behavior is a first-class requirement.
When infrastructure can fail, tests should drive:
- persisted failure state
- API error behavior
- emitted failure events

### Prefer simple, swappable infrastructure
Start with the smallest implementation that satisfies tests.
Keep infrastructure replaceable.
