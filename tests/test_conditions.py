from weather_agent import open_meteo
from weather_agent.conditions import CONDITIONS_EN, translate_condition


def test_every_condition_the_tools_can_return_has_an_english_translation():
    assert "parcialmente nublado" in CONDITIONS_EN
    missing = set(open_meteo.WMO_CONDITIONS.values()) - set(CONDITIONS_EN)
    assert missing == set()


def test_translate_condition_keeps_portuguese_and_unknown_values():
    assert translate_condition("parcialmente nublado", "pt") == "parcialmente nublado"
    assert translate_condition("parcialmente nublado", "en") == "partly cloudy"
    assert translate_condition("algo inesperado", "en") == "algo inesperado"
