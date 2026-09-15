// Tipo → Renderer (AC-06). Duas famílias: on_chat_model_* e on_tool_*. Qualquer outro
// Tipo lança erro.
//
// Pintura (AC-07): tokens de on_chat_model_stream concatenam no Rascunho — tokens de
// texto como texto, tokens de tool_call_chunks como a Tool Call em construção. O
// on_chat_model_end daquela Passada substitui o Rascunho — pelo Texto Final se a mensagem
// tem texto, e por Blocos de Tool Call se tem tool_calls. on_tool_start marca o Tool Call
// como executando; on_tool_end cria o Bloco Resultado da Tool.
//
// Todo StreamEvent, de qualquer Tipo, também vai para o painel Stream da resposta.

const RENDERERS = [
  [/^on_chat_model_/, renderChatModel],
  [/^on_tool_/, renderTool],
];

export function render(view, type, event) {
  const match = RENDERERS.find(([pattern]) => pattern.test(type));
  if (!match) throw new Error(`No renderer for event type: ${type}`);
  view.logEvent(type, event.name, summarize(type, event));
  // Todo StreamEvent nasce dentro de um nó do Grafo; o LangGraph anota qual.
  view.activateNode(event.metadata?.langgraph_node);
  match[1](view, type, event);
}

function renderChatModel(view, type, event) {
  switch (type) {
    case "on_chat_model_start":
      view.startPass();
      return;
    case "on_chat_model_stream": {
      const chunk = chunkOf(event);
      const text = textOf(chunk.content);
      if (text) view.appendDraft(text);
      for (const part of chunk.tool_call_chunks ?? []) {
        view.appendToolCallDraft(part.name ?? "", part.args ?? "");
      }
      return;
    }
    case "on_chat_model_end": {
      const message = outputOf(event);
      view.replaceDraftWithFinalText(textOf(message.content));
      if (message.tool_calls?.length) view.addToolCalls(message.tool_calls);
      else view.activateNode("__end__"); // sem Tool Call, tools_condition leva a END
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

// Uma linha por StreamEvent para o painel Stream.
function summarize(type, event) {
  switch (type) {
    case "on_chat_model_stream": {
      const chunk = chunkOf(event);
      const text = textOf(chunk.content);
      if (text) return JSON.stringify(text);
      const parts = chunk.tool_call_chunks ?? [];
      if (parts.length) {
        return parts
          .map((p) => `tool_call_chunk ${p.name ?? ""}${JSON.stringify(p.args ?? "")}`)
          .join(" ");
      }
      return "(empty chunk)";
    }
    case "on_chat_model_end": {
      const message = outputOf(event);
      if (message.tool_calls?.length) {
        return message.tool_calls.map((c) => `${c.name}(${JSON.stringify(c.args)})`).join(", ");
      }
      return JSON.stringify(textOf(message.content));
    }
    case "on_tool_start":
      return `input=${JSON.stringify(event.data.input)}`;
    case "on_tool_end":
      return `output=${outputOf(event).content}`;
    default:
      return "";
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
