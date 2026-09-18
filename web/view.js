// The agent's reply on screen: a sequence of Blocks (Tool Call, Tool Result, Text) plus a
// Stream Panel with every StreamEvent received. Renderers only talk to this interface; no
// DOM in renderers.js.

export function createResponseView(container, graphPanel) {
  const root = el("div", "response");
  container.appendChild(root);

  const stream = createStreamPanel(root);
  const toolsSlot = el("div", "response-tools");
  const messages = el("div", "response-text");
  const results = el("div", "response-results");
  root.append(toolsSlot, messages, results);
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
  const pendingResults = [];

  function scroll() {
    container.scrollTop = container.scrollHeight;
  }

  function ensureDraft() {
    if (draft) return;
    draft = el("div", "block block-text draft");
    messages.appendChild(draft);
  }

  function dropDraft() {
    draft?.remove();
    draft = null;
    toolCallDraft = null;
  }

  function flushPendingResults() {
    for (const block of pendingResults) results.appendChild(block);
    pendingResults.length = 0;
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
      flushPendingResults();
      scroll();
    },

    addToolCalls(toolCalls) {
      for (const call of toolCalls) {
        const block = el("details", "block block-tool-call");
        block.open = false;
        block.dataset.toolName = call.name;
        const summary = el("summary", "status");
        summary.textContent = "Tool call";
        block.appendChild(summary);
        block.appendChild(code(`${call.name}(${JSON.stringify(call.args)})`));
        toolsSlot.appendChild(block);
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
      const raw = el("details", "tool-json");
      const summary = el("summary", "");
      summary.textContent = "JSON";
      raw.appendChild(summary);
      raw.appendChild(code(prettyJson(content)));
      block.appendChild(raw);
      const weather = parseWeather(content);
      if (weather) block.appendChild(weatherCard(weather));
      pendingResults.push(block);
    },

    showError(message) {
      flushPendingResults();
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
  details.open = false;
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

function parseWeather(content) {
  try {
    const raw = typeof content === "string" ? JSON.parse(content) : content;
    if (!raw || typeof raw !== "object") return null;
    const city = raw.city;
    const temp = Number(raw.temp_c);
    if (typeof city !== "string" || !Number.isFinite(temp)) return null;
    return {
      city,
      tempC: temp,
      condition: typeof raw.condition === "string" ? raw.condition : "",
    };
  } catch {
    return null;
  }
}

function weatherCard(weather) {
  const card = el("div", "weather");
  const temp = el("div", "weather-temp");
  temp.append(String(Math.round(weather.tempC)));
  const unit = document.createElement("sup");
  unit.textContent = "°C";
  temp.appendChild(unit);
  const meta = el("div", "weather-meta");
  meta.appendChild(label(weather.condition || "—", "weather-cond"));
  meta.appendChild(label(weather.city, "weather-city"));
  card.append(temp, meta);
  return card;
}

function prettyJson(text) {
  try {
    return JSON.stringify(JSON.parse(text), null, 2);
  } catch {
    return String(text);
  }
}
