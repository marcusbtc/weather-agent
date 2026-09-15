"""Tools disponíveis ao modelo. Só existe `get_weather`, um stub sem HTTP (AC-03)."""

import asyncio

from langchain_core.tools import tool

WEATHER_DELAY_SECONDS = 2


@tool
async def get_weather(city: str) -> dict:
    """Consulta o clima atual de uma cidade."""
    await asyncio.sleep(WEATHER_DELAY_SECONDS)
    return {
        "city": city,
        "temp_c": 22,
        "condition": "parcialmente nublado",
    }


TOOLS = [get_weather]
