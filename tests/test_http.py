import httpx
import pytest
from langchain_core.messages import AIMessageChunk

from tests.fakes import parse_frame, stream_event
from weather_agent.main import create_app


def fake_run_agent(message: str):
    async def events():
        yield stream_event(
            "on_chat_model_stream",
            "fake",
            {"chunk": AIMessageChunk(content=f"eco: {message}")},
        )

    return events()


@pytest.fixture
async def client():
    transport = httpx.ASGITransport(app=create_app(run_agent=fake_run_agent))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


async def test_execute_streams_the_agent_events_as_sse(client):
    response = await client.post("/agent/execute", json={"message": "oi"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    event_line, payload = parse_frame(response.text)
    assert event_line == "event: on_chat_model_stream"
    assert payload["data"]["chunk"]["kwargs"]["content"] == "eco: oi"


async def test_root_serves_the_front(client):
    response = await client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert '<script type="module" src="./app.js">' in response.text


async def test_execute_rejects_a_body_without_message(client):
    response = await client.post("/agent/execute", json={})

    assert response.status_code == 422
