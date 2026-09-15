import { readSse } from "./sse.js";
import { render } from "./renderers.js";
import { appendUserMessage, createResponseView } from "./view.js";

const form = document.querySelector("#chat-form");
const input = document.querySelector("#message");
const sendButton = document.querySelector("#send");
const history = document.querySelector("#history");

form.addEventListener("submit", async (submit) => {
  submit.preventDefault();
  const message = input.value.trim();
  if (!message) return;

  input.value = "";
  setBusy(true);
  appendUserMessage(history, message);
  const view = createResponseView(history);

  try {
    await execute(message, view);
  } catch (error) {
    console.error(error);
    view.showError(error.message);
  } finally {
    setBusy(false);
    input.focus();
  }
});

// Cada Execução é independente: só a Mensagem atual vai ao servidor.
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

function setBusy(busy) {
  input.disabled = busy;
  sendButton.disabled = busy;
}
