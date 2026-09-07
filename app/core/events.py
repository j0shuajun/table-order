"""In-process Server-Sent Events broker for the admin dashboard.

Every subscribed admin holds one queue; publishing an event fans it out to all
subscribers. This is a single-process, in-memory broker — appropriate for the
single FastAPI deployment. Events are published from the event loop thread
after a successful DB commit.
"""

import asyncio
import json


class EventBroker:
    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue] = set()
        self._loop: asyncio.AbstractEventLoop | None = None

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Record the serving event loop so sync callers can publish safely."""
        self._loop = loop

    def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        self._subscribers.discard(queue)

    def publish(self, event: str, data: dict) -> None:
        """Fan out one event to all current subscribers (non-blocking).

        Route handlers run in a threadpool, so enqueueing is scheduled on the
        serving loop via ``call_soon_threadsafe`` to keep ``asyncio.Queue`` use
        thread-safe. Without a bound loop (e.g. unit tests) it enqueues directly.
        """
        message = {"event": event, "data": json.dumps(data, ensure_ascii=False)}
        for queue in list(self._subscribers):
            if self._loop is not None and self._loop.is_running():
                self._loop.call_soon_threadsafe(queue.put_nowait, message)
            else:
                queue.put_nowait(message)


# Module-level singleton shared across routers/services.
broker = EventBroker()
