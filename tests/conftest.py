import pytest


@pytest.fixture(autouse=True)
def stub_weather_source(monkeypatch):
    """The suite never depends on .env: importing weather_agent.main loads .env with
    override, and a local WEATHER_SOURCE=live would send the tests to the real Open-Meteo."""
    monkeypatch.setenv("WEATHER_SOURCE", "stub")
