"""HTTP (AC-01): `POST /agent/execute` chama o Agent e devolve o fluxo como SSE.

A rota não monta o Grafo nem itera o stream — só embrulha o que o Agent emite. O front
estático em `web/` é servido pela mesma app (ver docs/adr/0002).
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


class ExecuteBody(BaseModel):
    message: str


def create_app(run_agent: RunAgent = agent.run) -> FastAPI:
    app = FastAPI(title="Weather Agent")

    @app.post("/agent/execute")
    async def execute(body: ExecuteBody) -> StreamingResponse:
        return StreamingResponse(
            sse.encode(run_agent(body.message)),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache"},
        )

    if WEB_DIR.is_dir():
        app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")

    return app


# O .env da raiz é a fonte da chave (AC-09): vence um OPENAI_API_KEY herdado do shell.
load_dotenv(override=True)
app = create_app()
