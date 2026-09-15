# Clima real opcional, atrás de `WEATHER_SOURCE`, com o stub como padrão

O enunciado exige que `get_weather` seja um stub (AC-03: sem HTTP, `sleep ~2s`, sempre
22°C) e declara «HTTP de clima» fora de escopo. O autor quis, para uso próprio, ver dado
real. Adicionamos `weather_agent/open_meteo.py` (Open-Meteo, sem chave) e a variável
`WEATHER_SOURCE`, com **`stub` como padrão**: o repo continua cumprindo o AC-03 e o AC-08 sem
configuração; `live` é opt-in por `.env`, que é local e gitignored.

**Por que não trocar o stub:** o AC-08 valida «frase com 22°C» — com clima real isso só
passaria por coincidência. E o `sleep ~2s` do stub existe para o estado «executando…» ser
visível no front; a chamada real leva o tempo que levar.

**Consequência:** a Tool tem duas implementações atrás de um só nome e contrato
(`{"city", "temp_c", "condition"}`); Grafo, SSE e front não sabem qual está ativa.
