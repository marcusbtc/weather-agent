"""Encodes StreamEvents as Server-Sent Events (AC-05).

`event` = the StreamEvent's `event` field. `data` = the whole StreamEvent, serialized with
`langchain_core.load.dumps` (see docs/adr/0001). One `data:` line per event: `dumps`
emits no newlines, so every frame is exactly two lines.
"""

from collections.abc import AsyncIterator

from langchain_core.load import dumps
from langchain_core.runnables.schema import StreamEvent


def frame(event: StreamEvent) -> str:
    return f"event: {event['event']}\ndata: {dumps(event, ensure_ascii=False)}\n\n"


async def encode(events: AsyncIterator[StreamEvent]) -> AsyncIterator[str]:
    async for event in events:
        yield frame(event)
