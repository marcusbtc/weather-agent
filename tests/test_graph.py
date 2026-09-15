import json

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from tests.fakes import FINAL_TEXT, fake_weather_model
from weather_agent.graph import build_graph


async def test_graph_runs_the_tool_the_model_asked_for_and_returns_to_the_model():
    graph = build_graph(fake_weather_model())

    result = await graph.ainvoke(
        {"messages": [HumanMessage("Qual o clima em São Paulo?")]}
    )

    tool_messages = [m for m in result["messages"] if isinstance(m, ToolMessage)]
    assert len(tool_messages) == 1
    assert json.loads(tool_messages[0].content) == {
        "city": "São Paulo",
        "temp_c": 22,
        "condition": "parcialmente nublado",
    }

    last = result["messages"][-1]
    assert isinstance(last, AIMessage)
    assert last.content == FINAL_TEXT
