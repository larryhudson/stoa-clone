import asyncio

from app.infra.websocket_broadcaster import SessionEventBroadcaster


def test_unsubscribe_closes_subscription_even_when_queue_is_full():
    async def run_scenario() -> None:
        broadcaster = SessionEventBroadcaster()
        subscription = broadcaster.subscribe("session-1")

        for index in range(100):
            subscription.queue.put_nowait({"index": index})

        broadcaster.unsubscribe("session-1", subscription)
        await asyncio.sleep(0)

        queued = []
        while not subscription.queue.empty():
            queued.append(subscription.queue.get_nowait())

        assert queued[-1] is None

    asyncio.run(run_scenario())
