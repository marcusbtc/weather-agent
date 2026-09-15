"""Tools disponíveis ao modelo. Só existe `get_weather`.

Por padrão é o stub do enunciado (AC-03): sem HTTP, sleep ~2s, JSON fixo. Com
`WEATHER_SOURCE=live` no .env, consulta o clima real via Open-Meteo — fora do escopo do
enunciado, ligado só por escolha de quem roda.
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
        raise ValueError(f"WEATHER_SOURCE deve ser um de {WEATHER_SOURCES}, não {source!r}")
    return source


@tool
async def get_weather(city: str) -> dict:
    """Consulta o clima atual de uma cidade."""
    if weather_source() == "live":
        return await open_meteo.current_weather(city)

    await asyncio.sleep(WEATHER_DELAY_SECONDS)
    return {
        "city": city,
        "temp_c": 22,
        "condition": "parcialmente nublado",
    }


TOOLS = [get_weather]
