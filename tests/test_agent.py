from tests.fakes import FINAL_TEXT, fake_weather_model
from weather_agent.agent import describe_graph, make_model, run
from weather_agent.fake_model import FakeWeatherChatModel


def test_make_model_falls_back_to_the_fake_when_there_is_no_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("MODEL_SOURCE", raising=False)

    assert isinstance(make_model(), FakeWeatherChatModel)


def test_make_model_uses_the_fake_when_asked_even_with_an_api_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("MODEL_SOURCE", "fake")

    assert isinstance(make_model(), FakeWeatherChatModel)


def test_describe_graph_exposes_the_model_and_tools_nodes_and_their_edges():
    description = describe_graph(model=fake_weather_model())

    assert description["nodes"] == ["__start__", "model", "tools", "__end__"]
    assert {
        (e["source"], e["target"], e["conditional"]) for e in description["edges"]
    } == {
        ("__start__", "model", False),
        ("model", "tools", True),
        ("model", "__end__", True),
        ("tools", "model", False),
    }


async def test_agent_emits_only_chat_model_and_tool_events_in_execution_order():
    events = [
        e async for e in run("Qual o clima em São Paulo?", model=fake_weather_model())
    ]

    types = [e["event"] for e in events]
    assert set(types) <= {
        "on_chat_model_start",
        "on_chat_model_stream",
        "on_chat_model_end",
        "on_tool_start",
        "on_tool_end",
    }

    milestones = [t for t in types if t != "on_chat_model_stream"]
    assert milestones == [
        "on_chat_model_start",
        "on_chat_model_end",
        "on_tool_start",
        "on_tool_end",
        "on_chat_model_start",
        "on_chat_model_end",
    ]

    tool_end = next(e for e in events if e["event"] == "on_tool_end")
    assert tool_end["name"] == "get_weather"

    last_end = [e for e in events if e["event"] == "on_chat_model_end"][-1]
    assert last_end["data"]["output"].content == FINAL_TEXT
