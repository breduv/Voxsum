from time import perf_counter

from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import AIMessage
from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.graph import MessagesState
from loguru import logger

from app.clients.llm import invoke_model


async def call_model(
    state: MessagesState,
    config: RunnableConfig,
    *,
    model: Runnable[LanguageModelInput, AIMessage],
) -> dict[str, list[AIMessage]]:
    started = perf_counter()
    node = config.get("metadata", {}).get("langgraph_node", "assistant")
    logger.debug("LLM {}: requesting", node)
    response = await invoke_model(model, state["messages"], config=config)

    usage = response.usage_metadata or {}
    if usage:
        logger.debug(
            f"Tokens: in={usage.get('input_tokens')}, "
            f"out={usage.get('output_tokens')}",
        )
    logger.info(
        f"LLM {node}: response ({perf_counter() - started:.1f}s)",
    )

    return {"messages": [response]}
