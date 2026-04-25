from __future__ import annotations

import anyio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.domain.services import SessionService
from app.infra.websocket_broadcaster import SessionEventBroadcaster, SessionSubscription

router = APIRouter()


@router.websocket("/sessions/{session_id}/events/ws")
async def session_events(websocket: WebSocket, session_id: str, user_id: str | None = None) -> None:
    broadcaster: SessionEventBroadcaster = websocket.app.state.container.broadcaster
    session_service: SessionService = websocket.app.state.container.session_service
    subscription: SessionSubscription = broadcaster.subscribe(session_id)
    await websocket.accept()
    try:
        async with anyio.create_task_group() as task_group:
            task_group.start_soon(_forward_events, websocket, subscription)
            task_group.start_soon(_watch_for_disconnect, websocket, task_group.cancel_scope)
    finally:
        broadcaster.unsubscribe(session_id, subscription)
        if user_id is not None:
            session_service.leave_session(session_id, user_id)


async def _forward_events(websocket: WebSocket, subscription: SessionSubscription) -> None:
    while True:
        payload = await subscription.queue.get()
        if payload is None:
            return
        await websocket.send_json(payload)


async def _watch_for_disconnect(websocket: WebSocket, cancel_scope: anyio.CancelScope) -> None:
    try:
        while True:
            await websocket.receive()
    except (WebSocketDisconnect, RuntimeError):
        cancel_scope.cancel()
