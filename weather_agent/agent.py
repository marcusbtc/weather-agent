"""The Agent: compiles the Graph, calls `astream_events` and emits the StreamEvents
(AC-02/04).

Knows nothing about HTTP or SSE. The model is injectable for tests; by default it comes
from the environment.
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
    """OpenAI when there is a key; without one (or with MODEL_SOURCE=fake), the fake model —
    the Graph, the Tool and the stream stay real."""
    if os.environ.get("MODEL_SOURCE") == "fake" or not os.environ.get("OPENAI_API_KEY"):
        return FakeWeatherChatModel()

    # Reasoning-family model: it rejects `temperature`; `reasoning_effort="none"` minimizes
    # time to first token, which matters in an SSE chat.
    return ChatOpenAI(
        model=os.environ.get("OPENAI_MODEL", DEFAULT_MODEL),
        reasoning_effort="none",
    )


def describe_graph(model: BaseChatModel | None = None) -> dict:
    """Nodes and edges of the compiled Graph, for the front end to draw. Conditional edges
    are the ones leaving `tools_condition`."""
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
