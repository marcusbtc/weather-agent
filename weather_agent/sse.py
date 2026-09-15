"""Codifica StreamEvents como Server-Sent Events (AC-05).

`event` = o campo `event` do StreamEvent. `data` = o StreamEvent inteiro, serializado com
`langchain_core.load.dumps` (ver docs/adr/0001). Uma linha `data:` por evento: `dumps`
não produz quebras de linha, então cada frame é exatamente duas linhas.
"""

from collections.abc import AsyncIterator

from langchain_core.load import dumps
from langchain_core.runnables.schema import StreamEvent


def frame(event: StreamEvent) -> str:
    return f"event: {event['event']}\ndata: {dumps(event, ensure_ascii=False)}\n\n"


async def encode(events: AsyncIterator[StreamEvent]) -> AsyncIterator[str]:
    async for event in events:
        yield frame(event)
