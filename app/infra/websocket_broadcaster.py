from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from threading import Lock

from anyio import BrokenResourceError, ClosedResourceError, WouldBlock, create_memory_object_stream
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream


@dataclass(frozen=True)
class SessionSubscription:
    send_stream: MemoryObjectSendStream[dict]
    receive_stream: MemoryObjectReceiveStream[dict]


class SessionEventBroadcaster:
    def __init__(self) -> None:
        self._streams_by_session_id: dict[str, list[MemoryObjectSendStream[dict]]] = defaultdict(list)
        self._lock = Lock()

    def subscribe(self, session_id: str) -> SessionSubscription:
        send_stream, receive_stream = create_memory_object_stream[dict](100)
        with self._lock:
            self._streams_by_session_id[session_id].append(send_stream)
        return SessionSubscription(send_stream=send_stream, receive_stream=receive_stream)

    def unsubscribe(self, session_id: str, subscription: SessionSubscription) -> None:
        with self._lock:
            session_streams = self._streams_by_session_id.get(session_id, [])
            if subscription.send_stream in session_streams:
                session_streams.remove(subscription.send_stream)
            if not session_streams and session_id in self._streams_by_session_id:
                del self._streams_by_session_id[session_id]
        subscription.send_stream.close()

    def publish(self, session_id: str, payload: dict) -> None:
        with self._lock:
            session_streams = list(self._streams_by_session_id.get(session_id, []))
        for session_stream in session_streams:
            try:
                session_stream.send_nowait(payload)
            except (BrokenResourceError, ClosedResourceError, WouldBlock):
                continue
