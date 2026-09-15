"""Infra de teste: modelo falso, StreamEvents à mão e desmontagem de frames SSE."""

import json
import re

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, AIMessageChunk
from langchain_core.outputs import ChatGenerationChunk

FINAL_TEXT = "Em São Paulo faz 22°C, parcialmente nublado."


class ToolAwareFakeChatModel(GenericFakeChatModel):
    """GenericFakeChatModel não implementa bind_tools nem faz stream de tool_calls.

    Aqui bind_tools é aceito e ignorado, e uma AIMessage com tool_calls vira um único
    chunk com tool_call_chunks — como o ChatOpenAI real faz.
    """

    def bind_tools(self, tools, **kwargs):
        return self

    def _stream(self, messages, stop=None, run_manager=None, **kwargs):
        message = self._generate(messages, stop=stop, **kwargs).generations[0].message

        if message.tool_calls:
            chunks = [
                AIMessageChunk(
                    content="",
                    id=message.id,
                    tool_call_chunks=[
                        {
                            "id": tc["id"],
                            "name": tc["name"],
                            "args": json.dumps(tc["args"]),
                            "index": i,
                        }
                        for i, tc in enumerate(message.tool_calls)
                    ],
                )
            ]
        else:
            chunks = [
                AIMessageChunk(content=token, id=message.id)
                for token in re.split(r"(\s)", message.content)
            ]

        for chunk in chunks:
            generation = ChatGenerationChunk(message=chunk)
            if run_manager:
                run_manager.on_llm_new_token(chunk.content, chunk=generation)
            yield generation


def fake_weather_model() -> GenericFakeChatModel:
    """Decide chamar get_weather para São Paulo e depois responde com o Texto Final."""
    return ToolAwareFakeChatModel(
        messages=iter(
            [
                AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "id": "call_1",
                            "name": "get_weather",
                            "args": {"city": "São Paulo"},
                        }
                    ],
                ),
                AIMessage(content=FINAL_TEXT),
            ]
        )
    )


def stream_event(event: str, name: str, data: dict, run_id: str = "run-1") -> dict:
    """Um StreamEvent v2 montado à mão, com os metadados que o astream_events sempre traz."""
    return {
        "event": event,
        "name": name,
        "run_id": run_id,
        "tags": [],
        "metadata": {},
        "parent_ids": [],
        "data": data,
    }


def parse_frame(frame: str) -> tuple[str, dict]:
    """Desmonta um frame SSE em (linha event, data parseado)."""
    event_line, data_line = frame.rstrip("\n").split("\n")
    return event_line, json.loads(data_line.removeprefix("data: "))
