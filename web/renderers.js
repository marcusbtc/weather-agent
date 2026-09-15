// Event Type → Renderer (AC-06). Two families: on_chat_model_* and on_tool_*. Any other
// Event Type throws.
//
// Painting (AC-07): on_chat_model_stream tokens concatenate into the Draft — text tokens
// as text, tool_call_chunks as the Tool Call being assembled. That Pass's
// on_chat_model_end replaces the Draft — with the Final Text if the message has text, and
// with Tool Call Blocks if it has tool_calls. on_tool_start marks the Tool Call as running;
// on_tool_end creates the Tool Result Block.
//
// Every StreamEvent, of any Event Type, also goes to the reply's Stream Panel.

const RENDERERS = [
  [/^on_chat_model_/, renderChatModel],
  [/^on_tool_/, renderTool],
];

export function render(view, type, event) {
  const match = RENDERERS.find(([pattern]) => pattern.test(type));
  if (!match) throw new Error(`No renderer for event type: ${type}`);
  view.logEvent(type, event.name, summarize(type, event));
  // Every StreamEvent is born inside a Graph node; LangGraph records which one.
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
      else view.activateNode("__end__"); // no Tool Call: tools_condition leads to END
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

// One line per StreamEvent for the Stream Panel.
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

// The SSE `data` is the StreamEvent serialized with langchain_core.load.dumps (ADR-0001):
// LangChain messages arrive as {lc, type, id, kwargs}. Only these two accessors know that
// format.
function chunkOf(event) {
  return event.data.chunk.kwargs;
}

function outputOf(event) {
  return event.data.output.kwargs;
}

// A message's `content` may be a string or a list of parts {type: "text", text}.
function textOf(content) {
  if (typeof content === "string") return content;
  if (Array.isArray(content)) {
    return content
      .map((part) => (typeof part === "string" ? part : part.type === "text" ? part.text : ""))
      .join("");
  }
  return "";
}
