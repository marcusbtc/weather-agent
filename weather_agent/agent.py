"""O Agent: compila o Grafo, chama `astream_events` e emite os StreamEvents (AC-02/04).

Não conhece HTTP nem SSE. O modelo é injetável para testes; por padrão vem do ambiente.
"""

import os
from collections.abc import AsyncIterator

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_core.runnables.schema import StreamEvent
from langchain_openai import ChatOpenAI

from weather_agent.fake_model import FakeWeatherChatModel
from weather_agent.graph import build_graph

DEFAULT_MODEL = "gpt-5.4-mini"


def make_model() -> BaseChatModel:
    """OpenAI quando há chave; sem chave (ou com MODEL_SOURCE=fake), o modelo falso —
    o Grafo, a Tool e o stream continuam reais."""
    if os.environ.get("MODEL_SOURCE") == "fake" or not os.environ.get("OPENAI_API_KEY"):
        return FakeWeatherChatModel()

    # Família de reasoning: não aceita `temperature`; `reasoning_effort="none"` minimiza
    # a latência até o primeiro token, o que importa num chat em SSE.
    return ChatOpenAI(
        model=os.environ.get("OPENAI_MODEL", DEFAULT_MODEL),
        reasoning_effort="none",
    )


def describe_graph(model: BaseChatModel | None = None) -> dict:
    """Nós e arestas do Grafo compilado, para o front desenhar. Arestas condicionais são
    as que saem de `tools_condition`."""
    drawable = build_graph(model or make_model()).get_graph().to_json()
    return {
        "nodes": [node["id"] for node in drawable["nodes"]],
        "edges": [
            {
                "source": edge["source"],
                "target": edge["target"],
                "conditional": bool(edge.get("conditional", False)),
            }
            for edge in drawable["edges"]
        ],
    }


async def run(message: str, model: BaseChatModel | None = None) -> AsyncIterator[StreamEvent]:
    graph = build_graph(model or make_model())

    async for event in graph.astream_events(
        {"messages": [HumanMessage(message)]},
        version="v2",
        include_types=["chat_model", "tool"],
    ):
        yield event
