"""Admin SSE stream: one stream per admin, receives all store order events.

Auth is via ``?token=`` query param because EventSource cannot set headers.
A periodic keep-alive comment keeps intermediaries from dropping the stream.
"""

import asyncio

from fastapi import APIRouter, Query
from sse_starlette.sse import EventSourceResponse

from app.api.deps import claims_from_token
from app.core.events import broker

router = APIRouter(prefix="/api/admin", tags=["stream"])

_KEEPALIVE_SECONDS = 15


@router.get("/stream")
async def stream(token: str = Query(...)):
    claims_from_token(token, "admin")
    queue = broker.subscribe()

    async def event_generator():
        try:
            while True:
                try:
                    event = await asyncio.wait_for(
                        queue.get(), timeout=_KEEPALIVE_SECONDS
                    )
                    yield event
                except asyncio.TimeoutError:
                    yield {"event": "keep-alive", "data": ""}
        finally:
            broker.unsubscribe(queue)

    return EventSourceResponse(event_generator())
