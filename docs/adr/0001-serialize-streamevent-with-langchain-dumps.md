# Serialize the StreamEvent with `langchain_core.load.dumps`

AC-05 requires the `data` of every SSE frame to be the whole StreamEvent, serialized. The
event carries LangChain objects (`AIMessageChunk`, `ToolMessage`) that `json.dumps` cannot
serialize. We chose `langchain_core.load.dumps`, LangChain's canonical serialization,
over a `default=` hook calling `model_dump()`.

**Consequence:** messages reach the front end as `{lc, type, id, kwargs}`, so the
Renderers read `data.chunk.kwargs.content`, `data.output.kwargs.tool_calls`, etc. Changing
the serialization later means changing every Renderer — which is why `renderers.js` funnels
that knowledge through two accessors.

**Considered and rejected:** `json.dumps(event, default=lambda o: o.model_dump())` — a
flatter payload for the front end, but not the format LangChain itself uses for
`StreamEvent`, and `model_dump()` of an `AIMessageChunk` is not guaranteed stable across
versions.
