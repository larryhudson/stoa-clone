from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError


def receive_json_with_timeout(websocket, timeout: float = 5.0):
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(websocket.receive_json)
    try:
        return future.result(timeout=timeout)
    except FuturesTimeoutError as exc:
        future.cancel()
        raise AssertionError(
            f"timed out waiting for websocket JSON message within {timeout} seconds"
        ) from exc
    finally:
        executor.shutdown(wait=False, cancel_futures=True)
