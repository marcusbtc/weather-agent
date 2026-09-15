// Lê um body `text/event-stream` vindo de `fetch` (POST) e produz um frame por
// StreamEvent. EventSource só faz GET, por isso o parser é feito à mão.
//
// Cada frame produzido: { type, event } — `type` é a linha `event:` do SSE (o Tipo) e
// `event` é o StreamEvent inteiro, já parseado da linha `data:`.
//
// Se quem consome parar de iterar (por exemplo, um Renderer lançou erro), o reader é
// cancelado e a conexão fecha.

export async function* readSse(response) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      let separator;
      while ((separator = buffer.indexOf("\n\n")) !== -1) {
        const raw = buffer.slice(0, separator);
        buffer = buffer.slice(separator + 2);
        const frame = parseFrame(raw);
        if (frame) yield frame;
      }
    }
  } finally {
    reader.cancel().catch(() => {});
  }
}

function parseFrame(raw) {
  let type = "message";
  const dataLines = [];

  for (const line of raw.split("\n")) {
    if (line.startsWith("event:")) type = line.slice("event:".length).trim();
    else if (line.startsWith("data:")) dataLines.push(line.slice("data:".length).trimStart());
  }

  if (dataLines.length === 0) return null;
  return { type, event: JSON.parse(dataLines.join("\n")) };
}
