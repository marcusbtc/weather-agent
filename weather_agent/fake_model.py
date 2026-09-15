"""Modelo falso, sem LLM: o fallback quando não há OPENAI_API_KEY (ex.: demo na Vercel).

Faz o que um modelo de verdade faria neste Grafo, de forma determinística:
- diante da Mensagem do usuário, pede `get_weather` com a cidade que aparece depois de
  «em» («Qual o clima em Curitiba?» → Curitiba; sem cidade, São Paulo);
- diante do Resultado da Tool, responde «Em <cidade> faz <temp>°C, <condição>.»

Emite tokens em stream com um pequeno atraso para o Rascunho crescer visivelmente.
"""

import asyncio
import json
import re
import time
from collections.abc import AsyncIterator, Iterator
from typing import Any

from langchain_core.callbacks import AsyncCallbackManagerForLLMRun, CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult

DEFAULT_CITY = "São Paulo"
CITY_PATTERN = re.compile(r"\bem\s+([^?!.,;]+)", re.IGNORECASE)


class FakeWeatherChatModel(BaseChatModel):
    token_delay: float = 0.04

    @property
    def _llm_type(self) -> str:
        return "fake-weather"

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs) -> ChatResult:
        return ChatResult(generations=[ChatGeneration(message=self._decide(messages))])

    def _stream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        for chunk in self._chunks(self._decide(messages)):
            if run_manager:
                run_manager.on_llm_new_token(chunk.message.content, chunk=chunk)
            yield chunk
            time.sleep(self.token_delay)

    async def _astream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: AsyncCallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        for chunk in self._chunks(self._decide(messages)):
            if run_manager:
                await run_manager.on_llm_new_token(chunk.message.content, chunk=chunk)
            yield chunk
            await asyncio.sleep(self.token_delay)

    # ── decisão ──────────────────────────────────────────────────────────────────

    def _decide(self, messages: list[BaseMessage]) -> AIMessage:
        last = messages[-1]
        if isinstance(last, ToolMessage):
            return AIMessage(content=self._answer_from(last))
        return AIMessage(
            content="",
            tool_calls=[
                {
                    "id": "call_fake_1",
                    "name": "get_weather",
                    "args": {"city": self._city_in(str(last.content))},
                }
            ],
        )

    @staticmethod
    def _city_in(text: str) -> str:
        match = CITY_PATTERN.search(text)
        return match.group(1).strip() if match else DEFAULT_CITY

    @staticmethod
    def _answer_from(tool_message: ToolMessage) -> str:
        try:
            weather = json.loads(str(tool_message.content))
        except json.JSONDecodeError:
            return "Não consegui ler o resultado da tool."
        return f"Em {weather['city']} faz {weather['temp_c']}°C, {weather['condition']}."

    # ── stream ───────────────────────────────────────────────────────────────────

    @staticmethod
    def _chunks(message: AIMessage) -> list[ChatGenerationChunk]:
        if message.tool_calls:
            call = message.tool_calls[0]
            args = json.dumps(call["args"], ensure_ascii=False)
            pieces = [(call["name"], "")] + [("", piece) for piece in re.split(r'(?<=[{":])', args) if piece]
            return [
                ChatGenerationChunk(
                    message=AIMessageChunk(
                        content="",
                        tool_call_chunks=[
                            {"id": call["id"] if i == 0 else None, "name": name or None, "args": arg, "index": 0}
                        ],
                    )
                )
                for i, (name, arg) in enumerate(pieces)
            ]

        tokens = [t for t in re.split(r"(\s+)", str(message.content)) if t]
        return [ChatGenerationChunk(message=AIMessageChunk(content=token)) for token in tokens]
