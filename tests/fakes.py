"""Test infrastructure: the fake model with no delay, hand-built StreamEvents and SSE frame
parsing."""

import json

from weather_agent.fake_model import FakeWeatherChatModel

# What FakeWeatherChatModel answers to the get_weather stub for São Paulo (Portuguese
# question → Portuguese answer).
FINAL_TEXT = "Em São Paulo faz 22°C, parcialmente nublado."


def fake_weather_model() -> FakeWeatherChatModel:
    return FakeWeatherChatModel(token_delay=0)


def stream_event(event: str, name: str, data: dict, run_id: str = "run-1") -> dict:
    """A hand-built v2 StreamEvent, with the metadata astream_events always carries."""
    return {
        "event": event,
        "name": name,
        "run_id": run_id,
        "tags": [],
        "metadata": {},
        "parent_ids": [],
        "data": data,
    }


def parse_frame(frame: str) -> tuple[str, dict]:
    """Splits an SSE frame into (event line, parsed data)."""
    event_line, data_line = frame.rstrip("\n").split("\n")
    return event_line, json.loads(data_line.removeprefix("data: "))
