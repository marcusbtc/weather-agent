import pytest

from weather_agent import open_meteo
from weather_agent.tools import get_weather


async def test_get_weather_returns_the_stub_by_default(monkeypatch):
    monkeypatch.delenv("WEATHER_SOURCE", raising=False)

    result = await get_weather.ainvoke({"city": "São Paulo"})

    assert result == {
        "city": "São Paulo",
        "temp_c": 22,
        "condition": "parcialmente nublado",
    }


async def test_get_weather_uses_open_meteo_when_weather_source_is_live(monkeypatch):
    monkeypatch.setenv("WEATHER_SOURCE", "live")
    seen = []

    async def fake_current_weather(city: str) -> dict:
        seen.append(city)
        return {"city": "São Paulo, Brasil", "temp_c": 14.0, "condition": "chuvisco moderado"}

    monkeypatch.setattr(open_meteo, "current_weather", fake_current_weather)

    result = await get_weather.ainvoke({"city": "São Paulo"})

    assert seen == ["São Paulo"]
    assert result == {"city": "São Paulo, Brasil", "temp_c": 14.0, "condition": "chuvisco moderado"}


async def test_get_weather_rejects_an_unknown_weather_source(monkeypatch):
    monkeypatch.setenv("WEATHER_SOURCE", "banana")

    with pytest.raises(ValueError, match="WEATHER_SOURCE"):
        await get_weather.ainvoke({"city": "São Paulo"})
