# Optional live weather behind `WEATHER_SOURCE`, with the stub as default

The exercise requires `get_weather` to be a stub (AC-03: no HTTP, `sleep ~2s`, always 22°C)
and declares "weather HTTP" out of scope. The author wanted, for personal use, to see real
data. We added `weather_agent/open_meteo.py` (Open-Meteo, no key) and the `WEATHER_SOURCE`
variable, with **`stub` as the default**: the repo keeps satisfying AC-03 and AC-08 with no
configuration; `live` is opt-in via `.env`, which is local and gitignored.

**Why not replace the stub:** AC-08 checks for "a sentence with 22°C" — with live weather
that would only pass by coincidence. And the stub's `sleep ~2s` exists so the "running…"
state is visible in the front end; the real call takes however long it takes.

**Consequence:** the Tool has two implementations behind one name and one contract
(`{"city", "temp_c", "condition"}`); Graph, SSE and front end do not know which is active.
