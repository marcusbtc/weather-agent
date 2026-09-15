# Weather Agent — Praxis P1

Agent LangGraph com uma tool de clima (stub) e um chat em SSE. Um `POST /agent/execute`
recebe uma mensagem, roda o grafo (modelo ↔ tools) e devolve os `StreamEvent`s de
`astream_events` v2 como `text/event-stream`. O front lê o stream e pinta cada tipo de
evento como um estado separado: tool call, resultado da tool, texto.

## Requisitos

- Python 3.12+ e [`uv`](https://docs.astral.sh/uv/)
- Uma `OPENAI_API_KEY`

## Como subir API e front

```bash
cp .env.example .env        # e preencha OPENAI_API_KEY
uv sync
uv run uvicorn weather_agent.main:app --reload
```

Um processo só: a API fica em `http://127.0.0.1:8000/agent/execute` e o front em
`http://127.0.0.1:8000/`. Abra o front, pergunte «Qual o clima em São Paulo?» e veja o tool
call, o JSON do stub e a frase com 22°C aparecerem em sequência.

### Variáveis de ambiente (`.env` na raiz, gitignored)

| Variável          | Obrigatória | Padrão                          |
| ----------------- | ----------- | ------------------------------- |
| `OPENAI_API_KEY`  | sim         | —                               |
| `OPENAI_MODEL`    | não         | `gpt-5.4-mini`                  |
| `OPENAI_BASE_URL` | não         | API da OpenAI                   |
| `WEATHER_SOURCE`  | não         | `stub`                          |

Para usar um provedor compatível com a API da OpenAI (ex.: OpenRouter), aponte
`OPENAI_BASE_URL=https://openrouter.ai/api/v1` e use o id do modelo no formato do provedor
(`OPENAI_MODEL=openai/gpt-5.4-mini`), com a chave do provedor em `OPENAI_API_KEY`.

### Clima real (opcional, fora do enunciado)

O AC-03 pede um stub: `get_weather` sem HTTP, `sleep ~2s`, sempre 22°C «parcialmente
nublado». Esse é o padrão. Com `WEATHER_SOURCE=live` a tool consulta o clima real via
[Open-Meteo](https://open-meteo.com/) (geocodificação + condições atuais, sem chave),
mantendo o mesmo JSON `{"city", "temp_c", "condition"}`. Para a entrega avaliada pelos ACs,
deixe o padrão (`stub`).

O modelo padrão é da família de reasoning: não aceita `temperature`; usamos
`reasoning_effort="none"` para o primeiro token chegar rápido.

O `.env` da raiz vence variáveis já exportadas no shell (`load_dotenv(override=True)`): se
você tem um `OPENAI_API_KEY` antigo no `~/.zshenv`, a chave do `.env` é a que vale.

## Testar via curl

```bash
curl -N -X POST http://127.0.0.1:8000/agent/execute \
  -H 'Content-Type: application/json' \
  -d '{"message": "Qual o clima em São Paulo?"}'
```

Cada frame tem `event:` (o `event` do `StreamEvent`) e `data:` (o `StreamEvent` inteiro,
serializado com `langchain_core.load.dumps`):

```
event: on_chat_model_stream
data: {"event": "on_chat_model_stream", "name": "ChatOpenAI", "data": {"chunk": {"lc": 1, ...}}, ...}

event: on_tool_start
data: {"event": "on_tool_start", "name": "get_weather", "data": {"input": {"city": "São Paulo"}}, ...}
```

## Testes

```bash
uv run pytest
```

Os testes cobrem tool, grafo, agent, codificação SSE e rota HTTP com um modelo falso — não
chamam a OpenAI. A fumaça (AC-08) é manual: API no ar, `.env` preenchido, pergunta pelo
front ou pelo `curl` acima.

## Estrutura

```
weather_agent/
  tools.py    get_weather — stub sem HTTP, sleep ~2s, JSON fixo (ou live, por env)
  open_meteo.py  clima real via Open-Meteo, só com WEATHER_SOURCE=live
  graph.py    StateGraph: nó model ↔ nó tools (ToolNode + tools_condition)
  agent.py    compila o grafo e emite os StreamEvents de astream_events v2
  sse.py      StreamEvent → frame SSE (event + data)
  main.py     POST /agent/execute + front estático em /
web/
  index.html, styles.css
  app.js        formulário → fetch POST → loop de frames → render
  sse.js        parser de text/event-stream sobre fetch
  renderers.js  tipo de evento → renderer (on_chat_model_* | on_tool_*), senão erro
  view.js       blocos na tela: rascunho, tool call, resultado, texto final
tests/
docs/adr/       decisões de arquitetura
CONTEXT.md      glossário do domínio
```

## Como o front pinta (AC-06/07)

- `on_chat_model_start` abre um rascunho; `on_chat_model_stream` concatena tokens nele —
  tokens de texto como texto, `tool_call_chunks` como a tool call em construção
  (`get_weather({"city":"São Pa…`).
- `on_chat_model_end` substitui o rascunho daquela passada: por blocos de **tool call** se a
  mensagem tem `tool_calls`, pelo **texto final** se tem texto.
- `on_tool_start` marca o tool call como executando; `on_tool_end` cria o bloco
  **resultado da tool**.
- Qualquer outro tipo de evento lança erro, que aparece na tela.
- Cada resposta tem um painel **Stream** com uma linha por `StreamEvent` recebido (tipo,
  nome, resumo), na ordem de chegada — o mesmo que o `curl` mostra, na tela.

## Fora de escopo

Auth, persistência/checkpoint (cada mensagem é uma execução independente, sem memória),
RAG, AG-UI, stream custom, HTTP de clima real.
