"""Infra de teste: modelo falso sem atraso, StreamEvents à mão e desmontagem de frames SSE."""

import json

from weather_agent.fake_model import FakeWeatherChatModel

# O que o FakeWeatherChatModel responde ao stub de get_weather para São Paulo.
FINAL_TEXT = "Em São Paulo faz 22°C, parcialmente nublado."


def fake_weather_model() -> FakeWeatherChatModel:
    return FakeWeatherChatModel(token_delay=0)


def stream_event(event: str, name: str, data: dict, run_id: str = "run-1") -> dict:
    """Um StreamEvent v2 montado à mão, com os metadados que o astream_events sempre traz."""
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
    """Desmonta um frame SSE em (linha event, data parseado)."""
    event_line, data_line = frame.rstrip("\n").split("\n")
    return event_line, json.loads(data_line.removeprefix("data: "))
