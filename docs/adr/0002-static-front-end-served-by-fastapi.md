# Static front end served by FastAPI, no build step

The front end (`web/`) is plain HTML + JavaScript in ES modules, mounted at `/` by the same
FastAPI app that exposes `POST /agent/execute`. There is no bundler, no `node_modules`
and no compile step: a single `uv run uvicorn` brings up API and front end.

**Why:** the exercise has two front-end ACs (AC-06/07) about behaviour — dispatch by event
type and painting by state — and none about the stack. One process shrinks the delivery
surface ("a running repo") and removes a class of errors (CORS, two ports, two READMEs).

**Consequence:** no TypeScript and no front-end tests; the pure logic (SSE parser,
dispatch, view) lives in modules separate from the DOM to stay readable. The SSE parser is
hand-written because `EventSource` only does GET and the route is POST.

**Considered and rejected:** Vite + React + TypeScript in `web/` as a second process. More
ergonomic for growth, but the exercise does not grow.
