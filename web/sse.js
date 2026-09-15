// Reads a `text/event-stream` body coming from `fetch` (POST) and yields one frame per
// StreamEvent. EventSource only does GET, hence the hand-written parser.
//
// Each frame yielded: { type, event } — `type` is the SSE `event:` line (the Event Type)
// and `event` is the whole StreamEvent, already parsed from the `data:` line.
//
// If the consumer stops iterating (e.g. a Renderer threw), the reader is cancelled and the
// connection closes.

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
