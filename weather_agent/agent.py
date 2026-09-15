"""O Agent: compila o Grafo, chama `astream_events` e emite os StreamEvents (AC-02/04).

Não conhece HTTP nem SSE. O modelo é injetável para testes; por padrão vem do ambiente.
"""

import os
from collections.abc import AsyncIterator

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_core.runnables.schema import StreamEvent
from langchain_openai import ChatOpenAI

from weather_agent.graph import build_graph

DEFAULT_MODEL = "gpt-5.4-mini"


def make_model() -> BaseChatModel:
    # Família de reasoning: não aceita `temperature`; `reasoning_effort="none"` minimiza
    # a latência até o primeiro token, o que importa num chat em SSE.
    return ChatOpenAI(
        model=os.environ.get("OPENAI_MODEL", DEFAULT_MODEL),
        reasoning_effort="none",
    )


async def run(message: str, model: BaseChatModel | None = None) -> AsyncIterator[StreamEvent]:
    graph = build_graph(model or make_model())

    async for event in graph.astream_events(
        {"messages": [HumanMessage(message)]},
        version="v2",
        include_types=["chat_model", "tool"],
    ):
        yield event
