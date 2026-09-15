# Serializar o StreamEvent com `langchain_core.load.dumps`

O AC-05 exige que o `data` de cada frame SSE seja o StreamEvent inteiro serializado. O
evento carrega objetos LangChain (`AIMessageChunk`, `ToolMessage`) que `json.dumps` não
sabe serializar. Escolhemos `langchain_core.load.dumps`, a serialização canônica do
LangChain, em vez de um `default=` que chamasse `model_dump()`.

**Consequência:** as mensagens chegam ao front no formato `{lc, type, id, kwargs}`, então
os Renderers leem `data.chunk.kwargs.content`, `data.output.kwargs.tool_calls`, etc. Trocar
a serialização depois exige mudar todos os Renderers.

**Considerado e rejeitado:** `json.dumps(event, default=lambda o: o.model_dump())` — payload
mais raso para o front, mas não é o formato que o próprio LangChain usa para
`StreamEvent`, e `model_dump()` de um `AIMessageChunk` não é garantidamente estável entre
versões.
