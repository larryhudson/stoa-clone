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

### Domain knows events, not websockets
The domain may publish typed events.
It should not know about websocket connections or transport concerns.

Websocket broadcasting belongs in infrastructure / API layers.

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

### Be explicit about failure paths
Failure behavior is a first-class requirement.
When infrastructure can fail, tests should drive:
- persisted failure state
- API error behavior
- emitted failure events

### Prefer simple, swappable infrastructure
Start with the smallest implementation that satisfies tests.
Keep infrastructure replaceable.

