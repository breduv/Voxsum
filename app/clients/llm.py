from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx
from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import AIMessage
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_openai import ChatOpenAI
from openai import APIError, APITimeoutError, RateLimitError
from pydantic import SecretStr

from app.core.config import Settings
from app.core.errors import (
    ModelRateLimitError,
    ModelTimeoutError,
    ModelUnavailableError,
)


async def invoke_model(
    model: Runnable[LanguageModelInput, AIMessage],
    messages: LanguageModelInput,
    config: RunnableConfig | None = None,
) -> AIMessage:
    try:
        return await model.ainvoke(messages, config=config)
    except APITimeoutError as exc:
        raise ModelTimeoutError("Model request timed out") from exc
    except RateLimitError as exc:
        raise ModelRateLimitError("Model rate limit exceeded") from exc
    except APIError as exc:
        raise ModelUnavailableError("Model API request failed") from exc


@asynccontextmanager
async def create_llm(
    settings: Settings,
) -> AsyncGenerator[ChatOpenAI, None]:
    async with httpx.AsyncClient(
        proxy=(settings.proxy.get_secret_value() if settings.proxy else None),
        timeout=60.0,
    ) as http_client:
        model = ChatOpenAI(
            model=settings.llm_model,
            base_url=settings.api_base,
            api_key=settings.api_key or SecretStr("not-required"),
            http_async_client=http_client,
            http_socket_options=(),
            use_responses_api=False,
            timeout=60.0,
            max_retries=1,
        )

        yield model
