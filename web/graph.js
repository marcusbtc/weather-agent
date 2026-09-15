// Desenha o Grafo do Agent (GET /agent/graph) como SVG e acende o nó ativo.
//
// Layout em camadas, da esquerda para a direita: a camada de um nó é a sua distância em
// arestas a partir de __start__. Arestas condicionais (tools_condition) são tracejadas;
// arestas que voltam para uma camada anterior (tools → model) passam por baixo.

const NODE_W = 104;
const NODE_H = 36;
const LAYER_GAP = 72;
const ROW_GAP = 28;
const PAD = 16;

export async function createGraphPanel(container) {
  const response = await fetch("/agent/graph");
  if (!response.ok) throw new Error(`HTTP ${response.status} while loading the graph`);
  const graph = await response.json();

  const svg = draw(graph);
  container.appendChild(svg);

  let active = null;
  const edgesByPair = new Map(
    [...svg.querySelectorAll(".edge")].map((e) => [`${e.dataset.source}→${e.dataset.target}`, e]),
  );

  return {
    activate(nodeId) {
      if (!nodeId || nodeId === active) return;
      svg.querySelectorAll(".node.active").forEach((n) => n.classList.remove("active"));
      svg.querySelectorAll(".edge.active").forEach((e) => e.classList.remove("active"));

      const node = svg.querySelector(`.node[data-id="${cssEscape(nodeId)}"]`);
      if (node) node.classList.add("active");
      const edge = edgesByPair.get(`${active}→${nodeId}`);
      if (edge) edge.classList.add("active");
      active = nodeId;
    },

    reset() {
      active = null;
      svg.querySelectorAll(".active").forEach((n) => n.classList.remove("active"));
    },
  };
}

function draw({ nodes, edges }) {
  const layerOf = layers(nodes, edges);
  const rows = new Map(); // camada → ids na ordem
  for (const id of nodes) {
    const layer = layerOf.get(id);
    if (!rows.has(layer)) rows.set(layer, []);
    rows.get(layer).push(id);
  }
  const layerCount = Math.max(...rows.keys()) + 1;
  const rowCount = Math.max(...[...rows.values()].map((r) => r.length));

  const width = PAD * 2 + layerCount * NODE_W + (layerCount - 1) * LAYER_GAP;
  const height = PAD * 2 + rowCount * NODE_H + (rowCount - 1) * ROW_GAP + 24;

  const position = new Map();
  for (const [layer, ids] of rows) {
    const total = ids.length * NODE_H + (ids.length - 1) * ROW_GAP;
    const top = PAD + (height - 24 - PAD * 2 - total) / 2;
    ids.forEach((id, i) => {
      position.set(id, {
        x: PAD + layer * (NODE_W + LAYER_GAP),
        y: top + i * (NODE_H + ROW_GAP),
      });
    });
  }

  const svg = svgEl("svg", {
    viewBox: `0 0 ${width} ${height}`,
    width,
    height,
    class: "graph-svg",
    role: "img",
    "aria-label": "Agent graph",
  });

  const defs = svgEl("defs");
  defs.innerHTML = `
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" />
    </marker>`;
  svg.appendChild(defs);

  for (const edge of edges) {
    const from = position.get(edge.source);
    const to = position.get(edge.target);
    const back = layerOf.get(edge.target) <= layerOf.get(edge.source);
    const path = svgEl("path", {
      d: back ? backPath(from, to) : forwardPath(from, to),
      class: `edge${edge.conditional ? " conditional" : ""}`,
      "marker-end": "url(#arrow)",
      "data-source": edge.source,
      "data-target": edge.target,
    });
    svg.appendChild(path);
  }

  for (const id of nodes) {
    const { x, y } = position.get(id);
    const terminal = id === "__start__" || id === "__end__";
    const group = svgEl("g", { class: `node${terminal ? " terminal" : ""}`, "data-id": id });
    group.appendChild(
      svgEl("rect", { x, y, width: NODE_W, height: NODE_H, rx: terminal ? NODE_H / 2 : 8 }),
    );
    const text = svgEl("text", { x: x + NODE_W / 2, y: y + NODE_H / 2 + 4 });
    text.textContent = id.replaceAll("_", "");
    group.appendChild(text);
    svg.appendChild(group);
  }

  return svg;
}

// Camada = menor número de arestas desde __start__ (busca em largura).
function layers(nodes, edges) {
  const out = new Map();
  for (const e of edges) {
    if (!out.has(e.source)) out.set(e.source, []);
    out.get(e.source).push(e.target);
  }
  const layer = new Map([["__start__", 0]]);
  const queue = ["__start__"];
  while (queue.length) {
    const id = queue.shift();
    for (const next of out.get(id) ?? []) {
      if (layer.has(next)) continue;
      layer.set(next, layer.get(id) + 1);
      queue.push(next);
    }
  }
  const unreachable = Math.max(0, ...layer.values()) + 1;
  for (const id of nodes) if (!layer.has(id)) layer.set(id, unreachable);
  return layer;
}

function forwardPath(from, to) {
  const x1 = from.x + NODE_W;
  const y1 = from.y + NODE_H / 2;
  const x2 = to.x;
  const y2 = to.y + NODE_H / 2;
  const cx = (x1 + x2) / 2;
  return `M ${x1} ${y1} C ${cx} ${y1}, ${cx} ${y2}, ${x2} ${y2}`;
}

function backPath(from, to) {
  const x1 = from.x + NODE_W / 2;
  const y1 = from.y + NODE_H;
  const x2 = to.x + NODE_W / 2;
  const y2 = to.y + NODE_H;
  const dip = Math.max(y1, y2) + 34;
  return `M ${x1} ${y1} C ${x1} ${dip}, ${x2} ${dip}, ${x2} ${y2 + 2}`;
}

function svgEl(tag, attrs = {}) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  return node;
}

function cssEscape(value) {
  return typeof CSS !== "undefined" && CSS.escape ? CSS.escape(value) : value;
}
