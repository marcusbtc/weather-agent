import { readSse } from "./sse.js";
import { render } from "./renderers.js";
import { appendUserMessage, createResponseView } from "./view.js?v=11";
import { createGraphPanel } from "./graph.js";

const form = document.querySelector("#chat-form");
const input = document.querySelector("#message");
const sendButton = document.querySelector("#send");
const history = document.querySelector("#history");
const graphContainer = document.querySelector("#graph");
const graphVisibleToggle = document.querySelector("#graph-visible");
const emptyTemplate = document.querySelector("#empty-template");

const GRAPH_VISIBLE_KEY = "weather-agent:graph-visible";

let busy = false;

initGraphVisibility();
showEmpty();

// The Graph is the same for every Execution; load it once. If it fails, the chat goes on
// without the drawing.
const graphPanel = await createGraphPanel(graphContainer).catch((error) => {
  console.error(error);
  graphContainer.textContent = `Graph unavailable: ${error.message}`;
  return null;
});

form.addEventListener("submit", (submit) => {
  submit.preventDefault();
  void send(input.value);
});

async function send(raw) {
  const message = raw.trim();
  if (!message || busy) return;

  input.value = "";
  document.querySelector("#empty")?.remove();
  setBusy(true);
  appendUserMessage(history, message);
  const view = createResponseView(history, graphPanel);

  try {
    await execute(message, view);
  } catch (error) {
    console.error(error);
    view.showError(error.message);
  } finally {
    setBusy(false);
    input.focus();
  }
}

// Every Execution is independent: only the current Message goes to the server.
async function execute(message, view) {
  const response = await fetch("/agent/execute", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });

  if (!response.ok) throw new Error(`HTTP ${response.status}`);

  for await (const { type, event } of readSse(response)) {
    render(view, type, event);
  }
}

function setBusy(on) {
  busy = on;
  input.disabled = on;
  sendButton.disabled = on;
  history.querySelectorAll("[data-suggest]").forEach((button) => {
    button.disabled = on;
  });
}

function initGraphVisibility() {
  const stored = localStorage.getItem(GRAPH_VISIBLE_KEY);
  const visible = stored === null ? true : stored === "true";
  graphVisibleToggle.checked = visible;
  setGraphVisible(visible);

  graphVisibleToggle.addEventListener("change", () => {
    const show = graphVisibleToggle.checked;
    localStorage.setItem(GRAPH_VISIBLE_KEY, String(show));
    setGraphVisible(show);
  });
}

function setGraphVisible(visible) {
  graphContainer.hidden = !visible;
}

function showEmpty() {
  history.replaceChildren(emptyTemplate.content.cloneNode(true));
  bindSuggests();
}

function bindSuggests() {
  history.querySelectorAll("[data-suggest]").forEach((button) => {
    button.addEventListener("click", () => void send(button.dataset.suggest));
  });
}
