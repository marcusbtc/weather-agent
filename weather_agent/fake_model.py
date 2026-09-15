"""Modelo falso, sem LLM: o fallback quando não há OPENAI_API_KEY (ex.: demo na Vercel).

Faz o que um modelo de verdade faria neste Grafo, de forma determinística:
- diante da Mensagem do usuário, pede `get_weather` com a cidade que aparece depois de
  «em» ou «in» («Qual o clima em Curitiba?» → Curitiba; «weather in Lisbon?» → Lisbon;
  sem cidade, São Paulo);
- diante do Resultado da Tool, responde no idioma da pergunta:
  «Em <cidade> faz <temp>°C, <condição>.» ou «In <city> it's <temp>°C, <condition>.»

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
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage, HumanMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult

DEFAULT_CITY = "São Paulo"
CITY_PATTERN = re.compile(r"\b(em|in)\s+([^?!.,;]+)", re.IGNORECASE)
ANSWERS = {
    "pt": "Em {city} faz {temp_c}°C, {condition}.",
    "en": "In {city} it's {temp_c}°C, {condition}.",
}


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
        question = next((str(m.content) for m in reversed(messages) if isinstance(m, HumanMessage)), "")
        if isinstance(last, ToolMessage):
            return AIMessage(content=self._answer_from(last, self._language_of(question)))
        return AIMessage(
            content="",
            tool_calls=[
                {
                    "id": "call_fake_1",
                    "name": "get_weather",
                    "args": {"city": self._city_in(question or str(last.content))},
                }
            ],
        )

    @staticmethod
    def _city_in(text: str) -> str:
        match = CITY_PATTERN.search(text)
        return match.group(2).strip() if match else DEFAULT_CITY

    @staticmethod
    def _language_of(text: str) -> str:
        match = CITY_PATTERN.search(text)
        return "en" if match and match.group(1).lower() == "in" else "pt"

    @staticmethod
    def _answer_from(tool_message: ToolMessage, language: str) -> str:
        try:
            weather = json.loads(str(tool_message.content))
        except json.JSONDecodeError:
            return "Could not read the tool result." if language == "en" else "Não consegui ler o resultado da tool."
        return ANSWERS[language].format(**weather)

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
