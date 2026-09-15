import pytest


@pytest.fixture(autouse=True)
def stub_weather_source(monkeypatch):
    """A suíte nunca depende do .env: importar weather_agent.main carrega o .env com
    override, e um WEATHER_SOURCE=live local mandaria os testes ao Open-Meteo real."""
    monkeypatch.setenv("WEATHER_SOURCE", "stub")
