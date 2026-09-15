# Weather Agent

A LangGraph agent with a weather tool (a stub), exposed over HTTP as an SSE stream and
painted by a front end that renders each event type distinctly. Exercise P1 of Praxis
Founding, week 2.

## Language

### Execution

**Agent**:
The one that compiles the Graph and runs it for a Message, emitting StreamEvents. Knows
nothing about HTTP.
_Avoid_: bot, assistant, chain

**Graph**:
The model ↔ tools flow compiled by the Agent: the model node decides, the tools node
executes, and control returns to the model until there is no Tool Call left.
_Avoid_: pipeline, workflow

**Message**:
The single text the user sends in an Execution. Each Execution is independent; there is
no memory between them.
_Avoid_: prompt, question, turn

**Execution**:
One `POST /agent/execute` call from start to the end of the stream. It is born from a
Message and dies when the stream closes.
_Avoid_: session, conversation, request

**Tool**:
A function the model may ask to have called. Only `get_weather` exists here — by default a
stub with no HTTP and a fixed response.
_Avoid_: function, plugin, action

**Tool Call**:
The model's request to run a Tool with arguments. It is the outcome of a Pass that produced
no Final Text.
_Avoid_: function call, invocation

### Stream

**StreamEvent**:
One item emitted by `astream_events` v2: `event`, `name`, `data`, plus run metadata. The
unit that travels Agent → SSE → Front end without being reinterpreted.
_Avoid_: chunk, stream message, event (generic)

**Event Type**:
The `event` field of a StreamEvent (`on_chat_model_stream`, `on_tool_start`, ...). The only
key by which the Front end picks a Renderer.
_Avoid_: kind, category

**Pass**:
One round of the model node, delimited by `on_chat_model_start` and `on_chat_model_end`.
An Execution has one Pass per model decision: typically one that yields a Tool Call and
another that yields the Final Text.
_Avoid_: turn, iteration, step

### Painting

**Renderer**:
The Front-end function that knows how to paint one family of Event Types
(`on_chat_model_*` or `on_tool_*`). An Event Type outside those families is an error, not
silence.
_Avoid_: handler, view, component

**Draft**:
The concatenation of a Pass's `on_chat_model_stream` tokens, visible while the Pass has not
finished — text, or the Tool Call being assembled. Replaced whole at `on_chat_model_end`.
_Avoid_: buffer, partial, preview

**Final Text**:
The content of a Pass's complete message, received at `on_chat_model_end`. Replaces that
Pass's Draft.
_Avoid_: response, output

**Block**:
One visual unit of the agent's reply: Tool Call, Tool Result, or Text. Blocks appear in
sequence and never merge.
_Avoid_: card, item, row

**Tool Result**:
The `output` of `on_tool_end`, painted as its own Block, separate from the Tool Call that
produced it.
_Avoid_: return value, response

**Stream Panel**:
The list, inside a reply, of every StreamEvent received in arrival order. Shows the raw
flow; it is not a Block.
_Avoid_: log, console, debug
