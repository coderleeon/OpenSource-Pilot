"""OpenAI direct LLM client implementation."""

from __future__ import annotations

import openai
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.exceptions import ConfigurationError, LLMError
from app.core.logging import get_logger
from app.llm.base import LLMClient

logger = get_logger(__name__)


class OpenAIClient(LLMClient):
    """LLM client backed by the OpenAI API directly.

    Args:
        api_key: OpenAI API key.
        model: Model name (e.g. ``"gpt-4o-mini"``).

    Raises:
        ConfigurationError: If *api_key* is empty.
    """

    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise ConfigurationError(
                "OPENAI_API_KEY is not set",
                details="Set OPENAI_API_KEY in your .env file or environment.",
            )
        self._model = model
        self._client = openai.AsyncOpenAI(api_key=api_key)
        logger.info("openai_client_ready", model=model)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=30),
        retry=retry_if_exception_type(
            (openai.RateLimitError, openai.APITimeoutError, openai.APIConnectionError)
        ),
        reraise=True,
    )
    async def complete(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        """Send a chat completion request to OpenAI."""
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,  # type: ignore[arg-type]
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        except (openai.RateLimitError, openai.APITimeoutError, openai.APIConnectionError):
            raise
        except openai.AuthenticationError as exc:
            raise ConfigurationError(
                "OpenAI authentication failed — check OPENAI_API_KEY",
                details=str(exc),
            ) from exc
        except openai.OpenAIError as exc:
            raise LLMError(
                f"OpenAI API error with model {self._model!r}",
                details=str(exc),
            ) from exc
