"""HTTP (AC-01): `POST /agent/execute` calls the Agent and returns the flow as SSE.

The route neither builds the Graph nor iterates the stream — it only wraps what the Agent
emits. The static front end in `web/` is served by the same app (see docs/adr/0002).
"""

from collections.abc import AsyncIterator, Callable
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from langchain_core.runnables.schema import StreamEvent
from pydantic import BaseModel

from weather_agent import agent, sse

WEB_DIR = Path(__file__).resolve().parent.parent / "web"

RunAgent = Callable[[str], AsyncIterator[StreamEvent]]
DescribeGraph = Callable[[], dict]


class ExecuteBody(BaseModel):
    message: str


def create_app(
    run_agent: RunAgent = agent.run,
    describe_graph: DescribeGraph = agent.describe_graph,
) -> FastAPI:
    app = FastAPI(title="Weather Agent")

    @app.post("/agent/execute")
    async def execute(body: ExecuteBody) -> StreamingResponse:
        return StreamingResponse(
            sse.encode(run_agent(body.message)),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache"},
        )

    @app.get("/agent/graph")
    async def graph() -> dict:
        return describe_graph()

    if WEB_DIR.is_dir():
        app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")

    return app


# The root .env is the source of the key (AC-09): it wins over an OPENAI_API_KEY inherited
# from the shell.
load_dotenv(override=True)
app = create_app()
