import { readSse } from "./sse.js?v=3";
import { render } from "./renderers.js?v=3";
import { appendUserMessage, createResponseView } from "./view.js?v=11";
import { createGraphPanel } from "./graph.js?v=3";

const form = document.querySelector("#chat-form");
const input = document.querySelector("#message");
const sendButton = document.querySelector("#send");
const history = document.querySelector("#history");
const graphContainer = document.querySelector("#graph");
const graphVisibleToggle = document.querySelector("#graph-visible");
const newThreadButton = document.querySelector("#new-thread");
const threadList = document.querySelector("#thread-list");
const emptyTemplate = document.querySelector("#empty-template");

const sidebar = document.querySelector("#sidebar");
const sidebarOpen = document.querySelector("#sidebar-open");
const sidebarClose = document.querySelector("#sidebar-close");

const GRAPH_VISIBLE_KEY = "weather-agent:graph-visible";
const SIDEBAR_OPEN_KEY = "weather-agent:sidebar-open";
const THREADS_KEY = "weather-agent:threads";
const ACTIVE_THREAD_KEY = "weather-agent:active-thread";

let busy = false;
let threads = [];
let activeId = null;

initGraphVisibility();
initSidebar();
initThreads();

const graphPanel = await createGraphPanel(graphContainer).catch((error) => {
  console.error(error);
  graphContainer.textContent = `Graph unavailable: ${error.message}`;
  return null;
});

form.addEventListener("submit", (submit) => {
  submit.preventDefault();
  void send(input.value);
});

newThreadButton.addEventListener("click", () => {
  if (busy) return;
  createThread();
});

threadList.addEventListener("click", (event) => {
  const item = event.target.closest("[data-thread-id]");
  if (!item) return;
  openThread(item.dataset.threadId);
});

async function send(raw) {
  const message = raw.trim();
  if (!message || busy) return;

  if (!activeId) createThread();

  input.value = "";
  document.querySelector("#empty")?.remove();
  setBusy(true);
  appendUserMessage(history, message);
  snapshotActive();
  const view = createResponseView(history, graphPanel);

  try {
    await execute(message, view);
  } catch (error) {
    console.error(error);
    view.showError(error.message);
  } finally {
    setBusy(false);
    snapshotActive();
    input.focus();
  }
}

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
  newThreadButton.disabled = on;
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

function initSidebar() {
  const stored = localStorage.getItem(SIDEBAR_OPEN_KEY);
  setSidebarOpen(stored === null ? true : stored === "true");
  sidebarOpen.addEventListener("click", () => setSidebarOpen(true));
  sidebarClose.addEventListener("click", () => setSidebarOpen(false));
}

function setSidebarOpen(open) {
  sidebar.classList.toggle("is-collapsed", !open);
  sidebarOpen.setAttribute("aria-expanded", String(open));
  localStorage.setItem(SIDEBAR_OPEN_KEY, String(open));
}

function initThreads() {
  try {
    threads = JSON.parse(localStorage.getItem(THREADS_KEY) || "[]");
  } catch {
    threads = [];
  }
  if (!Array.isArray(threads)) threads = [];

  activeId = localStorage.getItem(ACTIVE_THREAD_KEY);
  if (!threads.some((thread) => thread.id === activeId)) activeId = threads[0]?.id ?? null;
  if (!activeId) {
    createThread();
    return;
  }
  renderHistory(threadById(activeId)?.html ?? "");
  paintThreadList();
}

function createThread() {
  snapshotActive();
  const thread = { id: uid(), title: "New thread", createdAt: Date.now(), html: "" };
  threads.unshift(thread);
  activeId = thread.id;
  renderHistory("");
  persistThreads();
  paintThreadList();
}

function openThread(id) {
  if (busy || !threadById(id)) return;
  if (id !== activeId) snapshotActive();
  activeId = id;
  renderHistory(threadById(id).html ?? "");
  persistThreads();
  paintThreadList();
}

function snapshotActive() {
  const thread = threadById(activeId);
  if (!thread) return;
  if (historyHasTurns()) {
    thread.html = history.innerHTML;
    thread.title = titleFrom(thread.html, thread.title);
  } else if (!hasTurns(thread.html)) {
    thread.html = "";
  }
  persistThreads();
  paintThreadList();
}

function renderHistory(html) {
  if (hasTurns(html)) {
    history.innerHTML = html;
    history.scrollTop = history.scrollHeight;
  } else {
    showEmpty();
  }
  bindSuggests();
}

function showEmpty() {
  history.replaceChildren(emptyTemplate.content.cloneNode(true));
}

function bindSuggests() {
  history.querySelectorAll("[data-suggest]").forEach((button) => {
    button.addEventListener("click", () => void send(button.dataset.suggest));
  });
}

function historyHasTurns() {
  return Boolean(history.querySelector(".user-message, .response"));
}

function hasTurns(html) {
  if (!html) return false;
  return html.includes("user-message") || html.includes("class=\"response\"") || html.includes("class='response'");
}

function paintThreadList() {
  threadList.replaceChildren();
  for (const thread of threads) {
    const item = document.createElement("button");
    item.type = "button";
    item.className = `thread-item${thread.id === activeId ? " is-active" : ""}`;
    item.dataset.threadId = thread.id;
    item.textContent = thread.title;
    threadList.appendChild(item);
  }
}

function persistThreads() {
  try {
    localStorage.setItem(THREADS_KEY, JSON.stringify(threads));
    if (activeId) localStorage.setItem(ACTIVE_THREAD_KEY, activeId);
  } catch (error) {
    console.error(error);
  }
}

function threadById(id) {
  return threads.find((thread) => thread.id === id);
}

function titleFrom(html, fallback) {
  const wrap = document.createElement("div");
  wrap.innerHTML = html;
  const text = wrap.querySelector(".user-message")?.textContent.trim();
  if (!text) return fallback;
  return text.length > 42 ? `${text.slice(0, 41)}…` : text;
}

function uid() {
  return `${Date.now().toString(16)}-${Math.random().toString(16).slice(2, 8)}`;
}
