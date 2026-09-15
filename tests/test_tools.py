from weather_agent.tools import get_weather


async def test_get_weather_returns_the_stub_for_the_asked_city():
    result = await get_weather.ainvoke({"city": "São Paulo"})

    assert result == {
        "city": "São Paulo",
        "temp_c": 22,
        "condition": "parcialmente nublado",
    }
