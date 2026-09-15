# Weather Agent

Agent LangGraph com uma tool de clima (stub), exposto por HTTP como um fluxo SSE e
pintado por um front que renderiza cada tipo de evento de forma distinta. Exercício P1
da Praxis Founding, semana 2.

## Language

### Execução

**Agent**:
Quem compila o Grafo e o executa para uma Mensagem, emitindo StreamEvents. Não conhece
HTTP.
_Avoid_: bot, assistente, chain

**Grafo**:
O fluxo modelo ↔ tools compilado pelo Agent: o nó de modelo decide, o nó de tools executa,
e volta ao modelo até não haver mais Tool Call.
_Avoid_: pipeline, workflow

**Mensagem**:
O texto único que o usuário envia numa Execução. Cada Execução é independente; não há
memória entre elas.
_Avoid_: prompt, pergunta, turno

**Execução**:
Uma chamada `POST /agent/execute` do início ao fim do stream. Nasce de uma Mensagem e
morre quando o stream fecha.
_Avoid_: sessão, conversa, request

**Tool**:
Função que o modelo pode pedir para ser chamada. Aqui só existe `get_weather`, um stub
sem HTTP com resposta fixa.
_Avoid_: função, plugin, action

**Tool Call**:
O pedido do modelo para executar uma Tool com argumentos. É o resultado de uma Passada
que não produziu texto final.
_Avoid_: function call, invocação

### Stream

**StreamEvent**:
Um item emitido por `astream_events` v2: `event`, `name`, `data`, e metadados de run.
É a unidade que atravessa Agent → SSE → Front sem ser reinterpretada.
_Avoid_: chunk, mensagem de stream, evento (genérico)

**Tipo**:
O campo `event` de um StreamEvent (`on_chat_model_stream`, `on_tool_start`, ...). É a
única chave pela qual o Front escolhe um Renderer.
_Avoid_: kind, categoria

**Passada**:
Uma rodada do nó de modelo, delimitada por `on_chat_model_start` e `on_chat_model_end`.
Uma Execução tem uma Passada por decisão do modelo: tipicamente uma que produz Tool Call
e outra que produz o Texto Final.
_Avoid_: turno, iteração, step

### Pintura

**Renderer**:
A função do Front que sabe pintar uma família de Tipos (`on_chat_model_*` ou
`on_tool_*`). Um Tipo fora dessas famílias é erro, não silêncio.
_Avoid_: handler, view, componente

**Rascunho**:
A concatenação dos tokens de `on_chat_model_stream` de uma Passada, visível enquanto a
Passada não terminou. Substituído inteiro pelo Texto Final no `on_chat_model_end`.
_Avoid_: buffer, parcial, preview

**Texto Final**:
O conteúdo da mensagem completa de uma Passada, recebido em `on_chat_model_end`. Substitui
o Rascunho daquela Passada.
_Avoid_: resposta, output

**Bloco**:
Uma unidade visual da resposta do agent: Tool Call, Resultado da Tool, ou Texto. Aparecem
em sequência, nunca se fundem.
_Avoid_: card, item, linha

**Resultado da Tool**:
O `output` de `on_tool_end`, pintado como um Bloco próprio, separado do Tool Call que o
originou.
_Avoid_: retorno, response
