from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass
from threading import Lock


@dataclass(frozen=True)
class SessionSubscription:
    loop: asyncio.AbstractEventLoop
    queue: asyncio.Queue[dict | None]


class SessionEventBroadcaster:
    def __init__(self) -> None:
        self._subscriptions_by_session_id: dict[str, list[SessionSubscription]] = defaultdict(list)
        self._lock = Lock()

    def subscribe(self, session_id: str) -> SessionSubscription:
        subscription = SessionSubscription(
            loop=asyncio.get_running_loop(),
            queue=asyncio.Queue(maxsize=100),
        )
        with self._lock:
            self._subscriptions_by_session_id[session_id].append(subscription)
        return subscription

    def unsubscribe(self, session_id: str, subscription: SessionSubscription) -> None:
        with self._lock:
            session_subscriptions = self._subscriptions_by_session_id.get(session_id, [])
            if subscription in session_subscriptions:
                session_subscriptions.remove(subscription)
            if not session_subscriptions and session_id in self._subscriptions_by_session_id:
                del self._subscriptions_by_session_id[session_id]

        try:
            subscription.loop.call_soon_threadsafe(self._close_subscription, subscription)
        except RuntimeError:
            return None

    def publish(self, session_id: str, payload: dict) -> None:
        with self._lock:
            session_subscriptions = list(self._subscriptions_by_session_id.get(session_id, []))

        for subscription in session_subscriptions:
            try:
                subscription.loop.call_soon_threadsafe(self._enqueue_payload, subscription, payload)
            except RuntimeError:
                continue

    def _enqueue_payload(self, subscription: SessionSubscription, payload: dict) -> None:
        try:
            subscription.queue.put_nowait(payload)
        except asyncio.QueueFull:
            return None

    def _close_subscription(self, subscription: SessionSubscription) -> None:
        while True:
            try:
                subscription.queue.put_nowait(None)
                return None
            except asyncio.QueueFull:
                try:
                    subscription.queue.get_nowait()
                except asyncio.QueueEmpty:
                    return None
