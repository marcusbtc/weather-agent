import json

import httpx
import pytest

from weather_agent.open_meteo import CityNotFound, current_weather

GEOCODING = {
    "results": [
        {
            "name": "São Paulo",
            "latitude": -23.5475,
            "longitude": -46.63611,
            "country": "Brasil",
        }
    ]
}

FORECAST = {
    "current": {"time": "2026-09-14T22:15", "temperature_2m": 14.0, "weather_code": 53},
}


def fake_open_meteo(geocoding: dict, forecast: dict) -> httpx.AsyncClient:
    def handle(request: httpx.Request) -> httpx.Response:
        if request.url.host == "geocoding-api.open-meteo.com":
            assert request.url.params["name"] == "São Paulo"
            return httpx.Response(200, json=geocoding)
        if request.url.host == "api.open-meteo.com":
            assert request.url.params["latitude"] == "-23.5475"
            assert request.url.params["longitude"] == "-46.63611"
            return httpx.Response(200, json=forecast)
        raise AssertionError(f"host inesperado: {request.url.host}")

    return httpx.AsyncClient(transport=httpx.MockTransport(handle))


async def test_current_weather_geocodes_the_city_and_reads_the_current_conditions():
    async with fake_open_meteo(GEOCODING, FORECAST) as client:
        result = await current_weather("São Paulo", client=client)

    assert result == {
        "city": "São Paulo, Brasil",
        "temp_c": 14.0,
        "condition": "chuvisco moderado",
    }


async def test_current_weather_rounds_the_temperature_to_one_decimal():
    forecast = json.loads(json.dumps(FORECAST))
    forecast["current"]["temperature_2m"] = 21.4567

    async with fake_open_meteo(GEOCODING, forecast) as client:
        result = await current_weather("São Paulo", client=client)

    assert result["temp_c"] == 21.5


async def test_current_weather_fails_clearly_when_the_city_is_unknown():
    async with fake_open_meteo({"results": []}, FORECAST) as client:
        with pytest.raises(CityNotFound, match="São Paulo"):
            await current_weather("São Paulo", client=client)
