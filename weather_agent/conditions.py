"""Weather condition labels by language.

The tools return conditions in Portuguese — the stub's label is fixed by AC-03 and the
Open-Meteo mapping follows it. Whoever writes the answer (the fake model, or the real model
via the system prompt) translates to the user's language; this is the fake model's table.
"""

CONDITIONS_EN = {
    "parcialmente nublado": "partly cloudy",
    "céu limpo": "clear sky",
    "predominantemente limpo": "mostly clear",
    "nublado": "overcast",
    "nevoeiro": "fog",
    "nevoeiro com geada": "freezing fog",
    "chuvisco leve": "light drizzle",
    "chuvisco moderado": "moderate drizzle",
    "chuvisco intenso": "dense drizzle",
    "chuvisco gelado leve": "light freezing drizzle",
    "chuvisco gelado intenso": "dense freezing drizzle",
    "chuva leve": "light rain",
    "chuva moderada": "moderate rain",
    "chuva forte": "heavy rain",
    "chuva gelada leve": "light freezing rain",
    "chuva gelada forte": "heavy freezing rain",
    "neve leve": "light snow",
    "neve moderada": "moderate snow",
    "neve forte": "heavy snow",
    "grãos de neve": "snow grains",
    "pancadas de chuva leves": "light rain showers",
    "pancadas de chuva moderadas": "moderate rain showers",
    "pancadas de chuva violentas": "violent rain showers",
    "pancadas de neve leves": "light snow showers",
    "pancadas de neve fortes": "heavy snow showers",
    "tempestade": "thunderstorm",
    "tempestade com granizo leve": "thunderstorm with light hail",
    "tempestade com granizo forte": "thunderstorm with heavy hail",
    "condição desconhecida": "unknown condition",
}


def translate_condition(condition: str, language: str) -> str:
    if language == "en":
        return CONDITIONS_EN.get(condition, condition)
    return condition
