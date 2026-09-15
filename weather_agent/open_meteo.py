"""Clima real via Open-Meteo (sem chave): geocodifica a cidade e lê as condições atuais.

Devolve o mesmo contrato do stub — {"city", "temp_c", "condition"} — para o Grafo e o
front não distinguirem a fonte. Só é usado quando WEATHER_SOURCE=live (ver tools.py);
o enunciado pede o stub.
"""

import httpx

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT_SECONDS = 10

# Códigos WMO 4677 usados pelo Open-Meteo em `weather_code`.
WMO_CONDITIONS = {
    0: "céu limpo",
    1: "predominantemente limpo",
    2: "parcialmente nublado",
    3: "nublado",
    45: "nevoeiro",
    48: "nevoeiro com geada",
    51: "chuvisco leve",
    53: "chuvisco moderado",
    55: "chuvisco intenso",
    56: "chuvisco gelado leve",
    57: "chuvisco gelado intenso",
    61: "chuva leve",
    63: "chuva moderada",
    65: "chuva forte",
    66: "chuva gelada leve",
    67: "chuva gelada forte",
    71: "neve leve",
    73: "neve moderada",
    75: "neve forte",
    77: "grãos de neve",
    80: "pancadas de chuva leves",
    81: "pancadas de chuva moderadas",
    82: "pancadas de chuva violentas",
    85: "pancadas de neve leves",
    86: "pancadas de neve fortes",
    95: "tempestade",
    96: "tempestade com granizo leve",
    99: "tempestade com granizo forte",
}


class CityNotFound(LookupError):
    pass


async def current_weather(city: str, client: httpx.AsyncClient | None = None) -> dict:
    if client is None:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as own_client:
            return await current_weather(city, client=own_client)

    place = await _geocode(city, client)
    current = await _current(place["latitude"], place["longitude"], client)

    label = place["name"]
    if place.get("country"):
        label = f"{label}, {place['country']}"

    return {
        "city": label,
        "temp_c": round(current["temperature_2m"], 1),
        "condition": WMO_CONDITIONS.get(current["weather_code"], "condição desconhecida"),
    }


async def _geocode(city: str, client: httpx.AsyncClient) -> dict:
    response = await client.get(
        GEOCODING_URL,
        params={"name": city, "count": 1, "language": "pt", "format": "json"},
    )
    response.raise_for_status()
    results = response.json().get("results") or []
    if not results:
        raise CityNotFound(f"Cidade não encontrada: {city}")
    return results[0]


async def _current(latitude: float, longitude: float, client: httpx.AsyncClient) -> dict:
    response = await client.get(
        FORECAST_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,weather_code",
            "timezone": "auto",
        },
    )
    response.raise_for_status()
    return response.json()["current"]
