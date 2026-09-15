from langchain_core.messages import AIMessageChunk, ToolMessage

from tests.fakes import fake_weather_model, parse_frame, stream_event
from weather_agent.agent import run
from weather_agent.sse import encode


async def _events():
    yield stream_event(
        "on_chat_model_stream",
        "ChatOpenAI",
        {"chunk": AIMessageChunk(content="Em São")},
    )
    yield stream_event(
        "on_tool_end",
        "get_weather",
        {
            "input": {"city": "São Paulo"},
            "output": ToolMessage(content='{"temp_c": 22}', tool_call_id="call_1"),
        },
        run_id="run-2",
    )


async def test_encode_writes_one_sse_frame_per_event_with_the_whole_event_as_data():
    frames = [f async for f in encode(_events())]

    assert len(frames) == 2
    for frame in frames:
        assert frame.endswith("\n\n")

    event_line, payload = parse_frame(frames[0])
    assert event_line == "event: on_chat_model_stream"
    assert payload["event"] == "on_chat_model_stream"
    assert payload["name"] == "ChatOpenAI"
    assert payload["data"]["chunk"]["kwargs"]["content"] == "Em São"

    event_line, payload = parse_frame(frames[1])
    assert event_line == "event: on_tool_end"
    assert payload["data"]["input"] == {"city": "São Paulo"}
    assert payload["data"]["output"]["kwargs"]["content"] == '{"temp_c": 22}'


async def test_encoded_agent_events_expose_the_fields_the_front_reads():
    """Front↔back contract: the paths renderers.js reads exist in real events."""
    frames = [
        f
        async for f in encode(run("Qual o clima em São Paulo?", model=fake_weather_model()))
    ]
    payloads = [parse_frame(f)[1] for f in frames]

    first_end, last_end = [p for p in payloads if p["event"] == "on_chat_model_end"]
    tool_call = first_end["data"]["output"]["kwargs"]["tool_calls"][0]
    assert tool_call["name"] == "get_weather"
    assert tool_call["args"] == {"city": "São Paulo"}
    assert last_end["data"]["output"]["kwargs"]["content"].startswith("Em São Paulo")

    tool_end = next(p for p in payloads if p["event"] == "on_tool_end")
    output = tool_end["data"]["output"]["kwargs"]
    # The front end pairs the Tool Call Block with its Result by this id.
    assert output["tool_call_id"] == tool_call["id"]
    assert '"temp_c": 22' in output["content"]

    tool_start = next(p for p in payloads if p["event"] == "on_tool_start")
    assert tool_start["name"] == "get_weather"
    assert tool_start["run_id"] == tool_end["run_id"]
