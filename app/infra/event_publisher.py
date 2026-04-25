from __future__ import annotations

from app.domain.events import serialize_event
from app.infra.websocket_broadcaster import SessionEventBroadcaster


class BroadcastingEventPublisher:
    def __init__(self, broadcaster: SessionEventBroadcaster) -> None:
        self.broadcaster = broadcaster

    def publish(self, event: object) -> None:
        self.broadcaster.publish(_session_id_for(event), serialize_event(event))


def _session_id_for(event: object) -> str:
    session_id = getattr(event, "session_id", None)
    if not isinstance(session_id, str):
        raise TypeError("event has no session_id")
    return session_id
