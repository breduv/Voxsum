import asyncio
from time import perf_counter

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph.state import CompiledStateGraph
from loguru import logger

from app.clients.llm import invoke_model
from app.core.errors import (
    EmptyRequestError,
    InvalidModelResponseError,
    ModelTimeoutError,
)


class ChatService:
    def __init__(self, graph: CompiledStateGraph, model: BaseChatModel):
        self.graph = graph
        self.model = model

    async def ensure_available(self) -> None:
        started = perf_counter()
        logger.debug("LLM: checking availability")
        try:
            async with asyncio.timeout(30):
                response = await invoke_model(
                    self.model,
                    [HumanMessage(content="Reply with only OK.")],
                )
        except TimeoutError as exc:
            raise ModelTimeoutError("Model availability check timed out") from exc

        if not isinstance(response, AIMessage) or not response.text.strip():
            raise InvalidModelResponseError("Model availability check returned no text")
        logger.info("LLM: available ({:.1f}s)", perf_counter() - started)

    async def summarize(self, transcript: str) -> str:
        text = transcript.strip()
        if not text:
            raise EmptyRequestError("Transcript is empty")

        # Each voice is independent: no conversation history or checkpoints.
        message = HumanMessage(
            content=f"Кратко перескажи, о чём тут речь. Старайся не упускать детали. Ответ оформи в Markdown:\n\n{text}"
        )
        result = await self.graph.ainvoke({"messages": [message]})
        messages = result.get("messages", [])
        if not messages or not isinstance(messages[-1], AIMessage):
            raise InvalidModelResponseError("Model returned no summary")

        summary = messages[-1].text.strip()
        if not summary:
            raise InvalidModelResponseError("Model returned an empty summary")
        return summary
