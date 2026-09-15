"""Tools available to the model. Only `get_weather` exists.

By default it is the exercise's stub (AC-03): no HTTP, sleep ~2s, fixed JSON. With
`WEATHER_SOURCE=live` in .env it fetches real weather from Open-Meteo — outside the
exercise's scope, enabled only by whoever runs it.
"""

import asyncio
import os

from langchain_core.tools import tool

from weather_agent import open_meteo

WEATHER_DELAY_SECONDS = 2
WEATHER_SOURCES = ("stub", "live")


def weather_source() -> str:
    source = os.environ.get("WEATHER_SOURCE", "stub")
    if source not in WEATHER_SOURCES:
        raise ValueError(f"WEATHER_SOURCE must be one of {WEATHER_SOURCES}, not {source!r}")
    return source


@tool
async def get_weather(city: str) -> dict:
    """Get the current weather for a city."""
    if weather_source() == "live":
        return await open_meteo.current_weather(city)

    await asyncio.sleep(WEATHER_DELAY_SECONDS)
    return {
        "city": city,
        "temp_c": 22,
        "condition": "parcialmente nublado",
    }


TOOLS = [get_weather]
