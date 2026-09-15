// The agent's reply on screen: a sequence of Blocks (Tool Call, Tool Result, Text) plus a
// Stream Panel with every StreamEvent received. Renderers only talk to this interface; no
// DOM in renderers.js.

export function createResponseView(container, graphPanel) {
  const root = el("div", "response");
  container.appendChild(root);

  const stream = createStreamPanel(root);
  graphPanel?.reset();
  graphPanel?.activate("__start__");

  // Draft of the current Pass, while it has not finished. Text and Tool Call being
  // assembled are the same Block: whatever arrives first sets the shape.
  let draft = null;
  let toolCallDraft = null; // { name, args } accumulated from tool_call_chunks

  // Tool Call Blocks still without a Result. on_tool_start does not carry the Tool Call
  // id, only the name and a run_id; on_tool_end carries tool_call_id and the same run_id.
  // So start pairs by name (first Block not yet started) and records the run_id, and end
  // resolves by tool_call_id, with run_id as fallback.
  const toolCallsById = new Map();
  const toolCallsByRunId = new Map();

  function scroll() {
    container.scrollTop = container.scrollHeight;
  }

  function ensureDraft() {
    if (draft) return;
    draft = el("div", "block block-text draft");
    root.appendChild(draft);
  }

  function dropDraft() {
    draft?.remove();
    draft = null;
    toolCallDraft = null;
  }

  return {
    logEvent(type, name, summary) {
      stream.add(type, name, summary);
    },

    activateNode(nodeId) {
      graphPanel?.activate(nodeId);
    },

    startPass() {
      ensureDraft();
      scroll();
    },

    appendDraft(text) {
      ensureDraft();
      draft.textContent += text;
      scroll();
    },

    appendToolCallDraft(name, args) {
      ensureDraft();
      if (!toolCallDraft) {
        toolCallDraft = { name: "", args: "" };
        draft.classList.add("block-tool-call");
        draft.appendChild(label("Tool call · assembling…", "status"));
        draft.appendChild(code(""));
      }
      toolCallDraft.name += name;
      toolCallDraft.args += args;
      draft.querySelector(".code").textContent = `${toolCallDraft.name}(${toolCallDraft.args}`;
      scroll();
    },

    replaceDraftWithFinalText(text) {
      if (toolCallDraft || !text) dropDraft();
      if (!text) return;
      ensureDraft();
      draft.textContent = text;
      draft.classList.remove("draft");
      draft = null;
      scroll();
    },

    addToolCalls(toolCalls) {
      for (const call of toolCalls) {
        const block = el("div", "block block-tool-call");
        block.dataset.toolName = call.name;
        block.appendChild(label("Tool call", "status"));
        block.appendChild(code(`${call.name}(${JSON.stringify(call.args)})`));
        root.appendChild(block);
        toolCallsById.set(call.id, block);
      }
      scroll();
    },

    markToolRunning(name, runId) {
      const block = [...toolCallsById.values()].find(
        (candidate) => candidate.dataset.toolName === name && !candidate.dataset.runId,
      );
      if (!block) return;
      block.dataset.runId = runId;
      toolCallsByRunId.set(runId, block);
      block.querySelector(".status").textContent = "Tool call · running…";
    },

    addToolResult({ toolCallId, runId, name }, content) {
      const callBlock = toolCallsById.get(toolCallId) ?? toolCallsByRunId.get(runId);
      if (callBlock) {
        callBlock.querySelector(".status").textContent = "Tool call";
        toolCallsById.delete(toolCallId);
        toolCallsByRunId.delete(runId);
      }

      const block = el("div", "block block-tool-result");
      block.appendChild(label(`Tool result · ${name}`, "status"));
      block.appendChild(code(prettyJson(content)));
      root.appendChild(block);
      scroll();
    },

    showError(message) {
      const block = el("div", "block block-error");
      block.textContent = message;
      root.appendChild(block);
      scroll();
    },
  };
}

// Collapsible panel with one line per StreamEvent, in arrival order.
function createStreamPanel(root) {
  const details = el("details", "stream");
  details.open = true;
  const summary = el("summary", "stream-summary");
  const list = el("ol", "stream-list");
  details.appendChild(summary);
  details.appendChild(list);
  root.appendChild(details);

  let count = 0;
  summary.textContent = "Stream · 0 events";

  return {
    add(type, name, text) {
      count += 1;
      summary.textContent = `Stream · ${count} event${count === 1 ? "" : "s"}`;

      const item = el("li", `stream-item ${type.startsWith("on_tool_") ? "is-tool" : "is-model"}`);
      item.appendChild(label(type, "stream-type"));
      item.appendChild(label(name, "stream-name"));
      item.appendChild(label(text, "stream-text"));
      list.appendChild(item);
      if (details.open) list.scrollTop = list.scrollHeight;
    },
  };
}

export function appendUserMessage(container, text) {
  const block = el("div", "user-message");
  block.textContent = text;
  container.appendChild(block);
  container.scrollTop = container.scrollHeight;
}

function el(tag, className) {
  const node = document.createElement(tag);
  node.className = className;
  return node;
}

function label(text, className) {
  const node = el("div", className);
  node.textContent = text;
  return node;
}

function code(text) {
  const node = el("pre", "code");
  node.textContent = text;
  return node;
}

function prettyJson(text) {
  try {
    return JSON.stringify(JSON.parse(text), null, 2);
  } catch {
    return String(text);
  }
}
