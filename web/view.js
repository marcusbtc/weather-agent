// A resposta do agent na tela: uma sequência de Blocos (Tool Call, Resultado da Tool,
// Texto). Os Renderers só falam com esta interface; nada de DOM em renderers.js.

export function createResponseView(container) {
  const root = el("div", "response");
  container.appendChild(root);

  let draft = null; // Bloco de texto da Passada corrente, enquanto não terminou

  // Blocos de Tool Call ainda sem Resultado. on_tool_start não traz o id da Tool Call,
  // só o nome e um run_id; on_tool_end traz tool_call_id e o mesmo run_id. Por isso o
  // start pareia por nome (primeiro Bloco ainda não iniciado) e registra o run_id, e o
  // end resolve por tool_call_id, com run_id como reserva.
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

  return {
    startPass() {
      ensureDraft();
      scroll();
    },

    appendDraft(text) {
      ensureDraft();
      draft.textContent += text;
      scroll();
    },

    replaceDraftWithFinalText(text) {
      if (!draft) {
        if (!text) return;
        ensureDraft();
      }
      if (text) {
        draft.textContent = text;
        draft.classList.remove("draft");
      } else {
        draft.remove();
      }
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
      block.querySelector(".status").textContent = "Tool call · executando…";
    },

    addToolResult({ toolCallId, runId, name }, content) {
      const callBlock = toolCallsById.get(toolCallId) ?? toolCallsByRunId.get(runId);
      if (callBlock) {
        callBlock.querySelector(".status").textContent = "Tool call";
        toolCallsById.delete(toolCallId);
        toolCallsByRunId.delete(runId);
      }

      const block = el("div", "block block-tool-result");
      block.appendChild(label(`Resultado · ${name}`, "status"));
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
