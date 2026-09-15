from tests.fakes import FINAL_TEXT, fake_weather_model
from weather_agent.agent import run


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
