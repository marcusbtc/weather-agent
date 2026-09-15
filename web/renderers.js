// Tipo → Renderer (AC-06). Duas famílias: on_chat_model_* e on_tool_*. Qualquer outro
// Tipo lança erro.
//
// Pintura (AC-07): tokens de on_chat_model_stream concatenam no Rascunho; o
// on_chat_model_end daquela Passada substitui o Rascunho — pelo Texto Final se a mensagem
// tem texto, e por Blocos de Tool Call se tem tool_calls. on_tool_start marca o Tool Call
// como executando; on_tool_end cria o Bloco Resultado da Tool.

const RENDERERS = [
  [/^on_chat_model_/, renderChatModel],
  [/^on_tool_/, renderTool],
];

export function render(view, type, event) {
  const match = RENDERERS.find(([pattern]) => pattern.test(type));
  if (!match) throw new Error(`Tipo sem Renderer: ${type}`);
  match[1](view, type, event);
}

function renderChatModel(view, type, event) {
  switch (type) {
    case "on_chat_model_start":
      view.startPass();
      return;
    case "on_chat_model_stream": {
      const text = textOf(chunkOf(event).content);
      if (text) view.appendDraft(text);
      return;
    }
    case "on_chat_model_end": {
      const message = outputOf(event);
      view.replaceDraftWithFinalText(textOf(message.content));
      if (message.tool_calls?.length) view.addToolCalls(message.tool_calls);
      return;
    }
    default:
      return;
  }
}

function renderTool(view, type, event) {
  switch (type) {
    case "on_tool_start":
      view.markToolRunning(event.name, event.run_id);
      return;
    case "on_tool_end": {
      const message = outputOf(event);
      view.addToolResult(
        { toolCallId: message.tool_call_id, runId: event.run_id, name: event.name },
        message.content,
      );
      return;
    }
    default:
      return;
  }
}

// O `data` do SSE é o StreamEvent serializado com langchain_core.load.dumps (ADR-0001):
// as mensagens LangChain chegam como {lc, type, id, kwargs}. Só estes dois acessores
// conhecem esse formato.
function chunkOf(event) {
  return event.data.chunk.kwargs;
}

function outputOf(event) {
  return event.data.output.kwargs;
}

// O `content` de uma mensagem pode ser string ou lista de partes {type: "text", text}.
function textOf(content) {
  if (typeof content === "string") return content;
  if (Array.isArray(content)) {
    return content
      .map((part) => (typeof part === "string" ? part : part.type === "text" ? part.text : ""))
      .join("");
  }
  return "";
}
